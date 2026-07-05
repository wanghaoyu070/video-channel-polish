#!/usr/bin/env python3
import argparse
import re
import subprocess
from pathlib import Path


DEFAULT_REPLACEMENTS = {
    "弦鱼": "闲鱼",
    "咸鱼": "闲鱼",
    "显于": "闲鱼",
    "行于": "闲鱼",
    "弦卡": "显卡",
    "碗杖": "网站",
    "成交纪录": "成交记录",
}


def timestamp(seconds: float) -> str:
    ms = int(round(max(0, seconds) * 1000))
    h, rem = divmod(ms, 3600000)
    m, rem = divmod(rem, 60000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def load_replacements(files):
    replacements = dict(DEFAULT_REPLACEMENTS)
    for file in files or []:
        path = Path(file).expanduser()
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=>" not in line:
                continue
            src, dst = line.split("=>", 1)
            replacements[src.strip()] = dst.strip()
    return replacements


def clean_text(text: str, replacements) -> str:
    text = re.sub(r"\s+", "", text.strip())
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text


def split_text(text: str, max_chars: int):
    if not text:
        return []
    raw, buf = [], ""
    for ch in text:
        buf += ch
        if ch in "，。！？；" and len(buf) >= 10:
            raw.append(buf)
            buf = ""
        elif len(buf) >= max_chars:
            raw.append(buf)
            buf = ""
    if buf:
        raw.append(buf)

    merged = []
    for piece in raw:
        if merged and (len(piece) <= 5 or len(merged[-1]) <= 8) and len(merged[-1] + piece) <= max_chars + 4:
            merged[-1] += piece
        else:
            merged.append(piece)
    return merged


def main():
    parser = argparse.ArgumentParser(description="Transcribe Chinese speech into corrected SRT subtitles.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--srt", required=True, type=Path)
    parser.add_argument("--transcript", type=Path)
    parser.add_argument("--workdir", type=Path, default=None)
    parser.add_argument("--model", default="small")
    parser.add_argument("--language", default="zh")
    parser.add_argument("--max-chars", type=int, default=20)
    parser.add_argument("--terms", action="append", default=[])
    args = parser.parse_args()

    try:
        from faster_whisper import WhisperModel
    except Exception as exc:
        raise SystemExit(f"faster_whisper is unavailable: {exc}")

    video = args.input.expanduser().resolve()
    srt = args.srt.expanduser().resolve()
    srt.parent.mkdir(parents=True, exist_ok=True)
    transcript = args.transcript.expanduser().resolve() if args.transcript else srt.with_suffix(".txt")
    workdir = args.workdir or Path(f"/tmp/social_video_polish_{video.stem}")
    workdir.mkdir(parents=True, exist_ok=True)
    audio = workdir / "transcribe_audio_16k.wav"

    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000", str(audio)], check=True)
    replacements = load_replacements(args.terms)
    model = WhisperModel(args.model, device="auto", compute_type="int8")
    segments, info = model.transcribe(str(audio), language=args.language, vad_filter=True, beam_size=5, word_timestamps=False)

    items = []
    for seg in segments:
        chunks = split_text(clean_text(seg.text, replacements), args.max_chars)
        if not chunks:
            continue
        duration = max(0.4, seg.end - seg.start)
        cur = seg.start
        total = sum(len(c) for c in chunks)
        for i, chunk in enumerate(chunks):
            end = seg.end if i == len(chunks) - 1 else cur + duration * (len(chunk) / total)
            if end - cur < 0.55 and i < len(chunks) - 1:
                end = min(seg.end, cur + 0.55)
            items.append([cur, end, chunk])
            cur = end

    merged = []
    for start, end, text in items:
        if merged and start - merged[-1][1] <= 0.08 and (len(text) <= 5 or len(merged[-1][2]) <= 8) and len(merged[-1][2] + text) <= args.max_chars + 4:
            merged[-1][1] = end
            merged[-1][2] += text
        else:
            merged.append([start, end, text])

    blocks = []
    for i, (start, end, text) in enumerate(merged, 1):
        blocks.append(f"{i}\n{timestamp(start)} --> {timestamp(end)}\n{text}\n")
    srt.write_text("\n".join(blocks), encoding="utf-8")
    transcript.write_text("\n".join(item[2] for item in merged), encoding="utf-8")
    print(f"language={info.language} probability={info.language_probability:.2f} entries={len(merged)}")
    print(srt)
    print(transcript)


if __name__ == "__main__":
    main()
