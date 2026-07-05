#!/usr/bin/env python3
import argparse
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def run(cmd):
    subprocess.run(cmd, check=True)


def pick_font():
    for candidate in [
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    ]:
        if Path(candidate).exists():
            return candidate
    raise SystemExit("No usable Chinese font found.")


def extract_frame(video: Path, seconds: float, out: Path):
    out.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-ss",
            str(seconds),
            "-i",
            str(video),
            "-frames:v",
            "1",
            str(out),
        ]
    )


def fit_font(draw, font_path, line1, line2, max_width, max_height):
    size1, size2 = 116, 108
    while True:
        font1 = ImageFont.truetype(font_path, size1)
        font2 = ImageFont.truetype(font_path, size2)
        b1 = draw.textbbox((0, 0), line1, font=font1, stroke_width=1)
        b2 = draw.textbbox((0, 0), line2, font=font2, stroke_width=1)
        w = max(b1[2] - b1[0], b2[2] - b2[0])
        h = (b1[3] - b1[1]) + (b2[3] - b2[1]) + 18
        if w <= max_width and h <= max_height:
            return font1, font2
        size1 -= 4
        size2 -= 4
        if size2 < 64:
            return font1, font2


def main():
    parser = argparse.ArgumentParser(description="Create a black-strip white-title cover from a video frame.")
    parser.add_argument("--video", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--time", type=float, default=3.0)
    parser.add_argument("--title-line1", default="别再手动存图了")
    parser.add_argument("--title-line2", default="商品素材一键入库")
    parser.add_argument("--bar-width-ratio", type=float, default=0.80)
    parser.add_argument("--bar-height-ratio", type=float, default=0.255)
    parser.add_argument("--bar-y-ratio", type=float, default=0.145)
    parser.add_argument("--frame", type=Path, default=None)
    args = parser.parse_args()

    video = args.video.expanduser().resolve()
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    frame = args.frame.expanduser().resolve() if args.frame else output.with_suffix(".frame.jpg")
    if not frame.exists():
        extract_frame(video, args.time, frame)

    img = Image.open(frame).convert("RGBA")
    width, height = img.size
    draw = ImageDraw.Draw(img)
    bar_w = int(width * args.bar_width_ratio)
    bar_h = int(height * args.bar_height_ratio)
    bar_x = (width - bar_w) // 2
    bar_y = int(height * args.bar_y_ratio)
    radius = max(18, int(height * 0.026))

    font1, font2 = fit_font(
        draw,
        pick_font(),
        args.title_line1,
        args.title_line2,
        bar_w - 110,
        bar_h - 44,
    )

    draw.rounded_rectangle(
        [bar_x, bar_y, bar_x + bar_w, bar_y + bar_h],
        radius=radius,
        fill=(0, 0, 0, 255),
    )

    b1 = draw.textbbox((0, 0), args.title_line1, font=font1, stroke_width=1)
    b2 = draw.textbbox((0, 0), args.title_line2, font=font2, stroke_width=1)
    h1, h2 = b1[3] - b1[1], b2[3] - b2[1]
    total_h = h1 + h2 + 18
    y1 = bar_y + (bar_h - total_h) // 2 - 6
    for text, font, bbox, y in [
        (args.title_line1, font1, b1, y1),
        (args.title_line2, font2, b2, y1 + h1 + 18),
    ]:
        text_w = bbox[2] - bbox[0]
        x = bar_x + (bar_w - text_w) // 2
        draw.text(
            (x, y),
            text,
            font=font,
            fill=(255, 255, 255, 255),
            stroke_width=1,
            stroke_fill=(255, 255, 255, 255),
        )

    img.convert("RGB").save(output, quality=96)
    print(output)


if __name__ == "__main__":
    main()
