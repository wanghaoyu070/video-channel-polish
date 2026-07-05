#!/usr/bin/env python3
import argparse
import bisect
import re
import subprocess
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def run(cmd, **kwargs):
    return subprocess.run(cmd, check=True, text=True, **kwargs)


def probe_size(path: Path):
    proc = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height",
            "-of",
            "csv=s=x:p=0",
            str(path),
        ],
        stdout=subprocess.PIPE,
    )
    width, height = proc.stdout.strip().split("x")
    return int(width), int(height)


def to_seconds(ts: str) -> float:
    h, m, s, ms = re.match(r"(\d+):(\d+):(\d+),(\d+)", ts).groups()
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def parse_srt(path: Path):
    text = path.read_text(encoding="utf-8-sig")
    blocks = re.split(r"\n\s*\n", text.strip())
    cues = []
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if len(lines) < 3:
            continue
        match = re.search(r"(\d+:\d+:\d+,\d+)\s*-->\s*(\d+:\d+:\d+,\d+)", block)
        if not match:
            continue
        cues.append((to_seconds(match.group(1)), to_seconds(match.group(2)), "".join(lines[2:])))
    return cues


def pick_font():
    for candidate in [
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/Library/Fonts/Arial Unicode.ttf",
    ]:
        if Path(candidate).exists():
            return candidate
    raise SystemExit("No usable Chinese font found.")


def main():
    parser = argparse.ArgumentParser(description="Burn SRT subtitles into a video using Pillow frame drawing.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--srt", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--font-size", type=int, default=48)
    parser.add_argument("--bottom-y-ratio", type=float, default=0.852)
    parser.add_argument("--crf", default="20")
    parser.add_argument("--preset", default="veryfast")
    args = parser.parse_args()

    video = args.input.expanduser().resolve()
    srt = args.srt.expanduser().resolve()
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    width, height = probe_size(video)
    frame_size = width * height * 3
    cues = parse_srt(srt)
    starts = [cue[0] for cue in cues]
    font = ImageFont.truetype(pick_font(), args.font_size)
    max_width = int(width * 0.78)
    bottom_y = int(height * args.bottom_y_ratio)

    def wrap_text(text, draw):
        lines, cur = [], ""
        for ch in text:
            test = cur + ch
            if draw.textbbox((0, 0), test, font=font)[2] <= max_width:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = ch
        if cur:
            lines.append(cur)
        if len(lines) > 2:
            lines = [lines[0], "".join(lines[1:])]
        return lines

    def draw_subtitle(img, text):
        draw = ImageDraw.Draw(img)
        lines = wrap_text(text, draw)
        if not lines:
            return img
        bboxes = [draw.textbbox((0, 0), line, font=font, stroke_width=3) for line in lines]
        widths = [b[2] - b[0] for b in bboxes]
        heights = [b[3] - b[1] for b in bboxes]
        line_gap = max(6, int(args.font_size * 0.16))
        pad_x, pad_y = int(args.font_size * 0.46), int(args.font_size * 0.21)
        total_h = sum(heights) + line_gap * (len(lines) - 1)
        y = bottom_y - total_h
        bg_w = max(widths) + pad_x * 2
        bg_h = total_h + pad_y * 2
        bg_x = (width - bg_w) // 2
        bg_y = y - pad_y + 2
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        od.rounded_rectangle([bg_x, bg_y, bg_x + bg_w, bg_y + bg_h], radius=8, fill=(0, 0, 0, 95))
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        draw = ImageDraw.Draw(img)
        for line, h, w in zip(lines, heights, widths):
            x = (width - w) // 2
            draw.text((x, y), line, font=font, fill=(255, 255, 255), stroke_width=3, stroke_fill=(0, 0, 0))
            y += h + line_gap
        return img

    reader = subprocess.Popen(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(video), "-vf", f"fps={args.fps},format=rgb24", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        stdout=subprocess.PIPE,
    )
    writer = subprocess.Popen(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-s",
            f"{width}x{height}",
            "-r",
            str(args.fps),
            "-i",
            "-",
            "-i",
            str(video),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "libx264",
            "-preset",
            args.preset,
            "-crf",
            args.crf,
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "copy",
            "-shortest",
            "-movflags",
            "+faststart",
            str(output),
        ],
        stdin=subprocess.PIPE,
    )

    frame_no = 0
    last_report = time.time()
    try:
        while True:
            raw = reader.stdout.read(frame_size)
            if not raw or len(raw) != frame_size:
                break
            t = frame_no / args.fps
            idx = bisect.bisect_right(starts, t) - 1
            img = Image.frombytes("RGB", (width, height), raw)
            if idx >= 0:
                start, end, text = cues[idx]
                if start <= t <= end:
                    img = draw_subtitle(img, text)
            writer.stdin.write(img.tobytes())
            frame_no += 1
            now = time.time()
            if now - last_report > 20:
                print(f"processed {frame_no} frames / {frame_no / args.fps:.1f}s", flush=True)
                last_report = now
    finally:
        if writer.stdin:
            writer.stdin.close()
        writer_rc = writer.wait()
        reader_rc = reader.wait()
        if writer_rc or reader_rc:
            raise SystemExit(f"ffmpeg failed reader={reader_rc} writer={writer_rc}")
    print(f"written={output} frames={frame_no} duration={frame_no / args.fps:.2f}s")


if __name__ == "__main__":
    main()
