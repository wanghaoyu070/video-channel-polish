#!/usr/bin/env python3
import argparse
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Prepend a silent static cover image to a video.")
    parser.add_argument("--cover", required=True, type=Path)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--duration", type=float, default=1.5)
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--crf", default="20")
    parser.add_argument("--preset", default="veryfast")
    args = parser.parse_args()

    cover = args.cover.expanduser().resolve()
    src = args.input.expanduser().resolve()
    out = args.output.expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    filter_complex = (
        f"[0:v]fps={args.fps},format=yuv420p,scale={args.width}:{args.height},setsar=1[v0];"
        f"[2:v]fps={args.fps},format=yuv420p,scale={args.width}:{args.height},setsar=1[v1];"
        "[1:a]aresample=48000[a0];"
        "[2:a]aresample=48000[a1];"
        "[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]"
    )
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-y",
            "-loop",
            "1",
            "-t",
            str(args.duration),
            "-i",
            str(cover),
            "-f",
            "lavfi",
            "-t",
            str(args.duration),
            "-i",
            "anullsrc=channel_layout=stereo:sample_rate=48000",
            "-i",
            str(src),
            "-filter_complex",
            filter_complex,
            "-map",
            "[v]",
            "-map",
            "[a]",
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
        ],
        check=True,
    )
    print(out)


if __name__ == "__main__":
    main()
