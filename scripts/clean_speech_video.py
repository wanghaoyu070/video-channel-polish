#!/usr/bin/env python3
import argparse
import re
import subprocess
from pathlib import Path


def run(cmd, **kwargs):
    return subprocess.run(cmd, check=True, text=True, **kwargs)


def probe_duration(path: Path) -> float:
    proc = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        stdout=subprocess.PIPE,
    )
    return float(proc.stdout.strip())


def detect_silences(audio: Path, noise: str, min_duration: float):
    proc = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-nostats",
            "-i",
            str(audio),
            "-af",
            f"silencedetect=noise={noise}:d={min_duration}",
            "-f",
            "null",
            "-",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    text = proc.stdout + proc.stderr
    starts, ends = [], []
    for line in text.splitlines():
        m = re.search(r"silence_start: ([0-9.]+)", line)
        if m:
            starts.append(float(m.group(1)))
        m = re.search(r"silence_end: ([0-9.]+) \| silence_duration: ([0-9.]+)", line)
        if m:
            ends.append((float(m.group(1)), float(m.group(2))))
    silences = []
    for start, (end, duration) in zip(starts, ends):
        if end > start and duration >= min_duration:
            silences.append((start, end, duration))
    return silences


def build_segments(duration: float, silences, keep_pause: float):
    segments = []
    cur = 0.0
    for start, end, _ in silences:
        cut_start = start if start < 0.5 else min(end, start + keep_pause)
        if cut_start > cur + 0.04:
            segments.append((cur, cut_start))
        cur = max(cur, end)
    if cur < duration - 0.04:
        segments.append((cur, duration))

    merged = []
    for start, end in segments:
        if end - start < 0.08:
            continue
        if merged and start - merged[-1][1] < 0.02:
            merged[-1] = (merged[-1][0], end)
        else:
            merged.append((start, end))
    return merged


def main():
    parser = argparse.ArgumentParser(description="Remove long speech pauses and lightly speed up a video.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--workdir", type=Path, default=None)
    parser.add_argument("--noise", default="-35dB")
    parser.add_argument("--silence-duration", type=float, default=0.35)
    parser.add_argument("--keep-pause", type=float, default=0.12)
    parser.add_argument("--speed", type=float, default=1.05)
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument("--crf", default="20")
    parser.add_argument("--preset", default="veryfast")
    args = parser.parse_args()

    src = args.input.expanduser().resolve()
    out = args.output.expanduser().resolve()
    workdir = args.workdir or Path(f"/tmp/social_video_polish_{src.stem}")
    workdir.mkdir(parents=True, exist_ok=True)
    out.parent.mkdir(parents=True, exist_ok=True)

    audio = workdir / "source_audio_16k.wav"
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(src), "-vn", "-ac", "1", "-ar", "16000", str(audio)])

    duration = probe_duration(src)
    silences = detect_silences(audio, args.noise, args.silence_duration)
    segments = build_segments(duration, silences, args.keep_pause)
    if not segments:
        raise SystemExit("No keep segments generated; aborting.")

    filters, parts = [], []
    for i, (start, end) in enumerate(segments):
        filters.append(f"[0:v:0]trim=start={start:.3f}:end={end:.3f},setpts=PTS-STARTPTS[v{i}]")
        filters.append(f"[0:a:0]atrim=start={start:.3f}:end={end:.3f},asetpts=PTS-STARTPTS[a{i}]")
        parts.append(f"[v{i}][a{i}]")
    filters.append("".join(parts) + f"concat=n={len(segments)}:v=1:a=1[vcat][acat]")
    filters.append(f"[vcat]setpts=PTS/{args.speed},scale=-2:{args.height}[vout]")
    filters.append(f"[acat]atempo={args.speed},aresample=48000[aout]")

    kept = sum(end - start for start, end in segments)
    print(f"silences={len(silences)} segments={len(segments)} source_duration={duration:.2f}s")
    print(f"estimated_final={kept / args.speed:.2f}s")

    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-y",
            "-i",
            str(src),
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[vout]",
            "-map",
            "[aout]",
            "-c:v",
            "libx264",
            "-preset",
            args.preset,
            "-crf",
            args.crf,
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-movflags",
            "+faststart",
            str(out),
        ]
    )
    print(out)


if __name__ == "__main__":
    main()
