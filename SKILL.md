---
name: video-channel-polish
description: "End-to-end Chinese social-video workflow for screen-recorded talking-head demos: analyze raw videos, remove stalls and repeated speech, normalize pacing, transcribe and burn subtitles, make black-background white-title covers from early video frames, write publish copy, and safely clean generated variants. Use when the user asks to process 视频号/短视频/口播录屏素材, polish a recorded demo, add or adjust subtitles, make a cover, prepare publish metadata, or turn the current video-editing flow into repeatable outputs."
---

# Video Channel Polish

Polish a raw screen-recorded demo into publish-ready artifacts while preserving originals. This skill specializes the generic social-video workflow for the user's preferred 视频号 style.

## Workflow

1. **Inspect source**
   - Run `ffprobe` on the source or current final video.
   - Create a task directory under `/tmp/video_channel_polish_<stem>`.
   - Never overwrite the original source or prior accepted output.

2. **Analyze speech**
   - Detect long pauses with FFmpeg `silencedetect`.
   - Transcribe with `scripts/transcribe_subtitle.py` when content decisions or subtitles are needed.
   - Identify false starts, repeated ideas, and end-of-video rambles before automated cutting.

3. **Create clean base video**
   - For first-pass polishing, remove obvious repeated sections with FFmpeg trim/concat.
   - Run `scripts/clean_speech_video.py` to compress pauses and lightly speed speech.
   - Use `--speed 1.05` unless the user asks for a faster style.
   - Verify duration, dimensions, audio, and a few preview frames.

4. **Add subtitles**
   - Generate or reuse an SRT from the clean base video.
   - Fix recurring ASR terms before burn-in.
   - Burn subtitles from the clean base video, not an already subtitled video.
   - For this user's current preference, use `--font-size 42 --bottom-y-ratio 0.92`.

5. **Make cover**
   - Use `scripts/make_black_title_cover.py` for the preferred cover style.
   - Pick a frame from the first `0-5s` where the product page or system UI is clear and the person remains visible at lower right.
   - Default title:
     - `别再手动存图了`
     - `商品素材一键入库`
   - Output a standalone PNG by default.
   - Only prepend a cover intro if the user explicitly asks.

6. **Publish metadata**
   - When the user is publishing, prepare two separate copy sets by default: 小红书 and 微信视频号.
   - For each platform, provide title, description/caption, and topic tags when applicable.
   - Keep copy concrete: problem, workflow, result, and one lesson learned.

7. **Cleanup**
   - Move rejected/generated variants to Trash with `scripts/safe_cleanup.py`.
   - Keep source, accepted final videos, final cover PNG, and corrected SRT/transcript.

## Commands

```bash
python scripts/clean_speech_video.py --input raw.mp4 --output clean_1080p.mp4 --speed 1.05 --height 1080
python scripts/transcribe_subtitle.py --input clean_1080p.mp4 --srt subtitles.srt --transcript transcript.txt --model small --language zh --max-chars 18
python scripts/burn_subtitles.py --input clean_1080p.mp4 --srt subtitles.srt --output subtitled.mp4 --font-size 42 --bottom-y-ratio 0.92
python scripts/make_black_title_cover.py --video clean_1080p.mp4 --time 3 --output cover.png --title-line1 "别再手动存图了" --title-line2 "商品素材一键入库"
python scripts/prepend_cover.py --cover cover.png --input subtitled.mp4 --output with_cover_intro.mp4 --duration 1.2 --width 1720 --height 1080
python scripts/safe_cleanup.py --keep final.mp4 --keep cover.png --candidates rejected.mp4
```

## Style Defaults

Read `references/style_defaults.md` before choosing subtitle placement, cover wording, publish-copy format, or cleanup behavior for this user.

## Verification

Always verify final artifacts:

```bash
ffprobe -v error -show_entries format=duration,size:stream=width,height,avg_frame_rate,codec_name,codec_type,sample_rate -of json final.mp4
ffmpeg -hide_banner -loglevel error -y -ss 00:00:03 -i final.mp4 -frames:v 1 /tmp/preview_start.jpg
ffmpeg -hide_banner -loglevel error -y -ss 00:03:00 -i final.mp4 -frames:v 1 /tmp/preview_late.jpg
```

Open preview frames visually before final handoff.
