# Video Channel Polish Style Defaults

Use these defaults for Chinese screen-recorded talking-head demos intended for 视频号 or similar social feeds.

## Speech Cut

- Preserve the original source.
- Remove obvious false starts and repeated sentences before automated silence compression.
- Compress pauses with `clean_speech_video.py`.
- Use `--speed 1.05` for a natural 视频号 pace. Avoid `1.15+` unless the user asks for a fast style.
- Export the clean base video at the same practical aspect ratio as the source; for this workflow, `1720x1080` is acceptable when the source already has that ratio after 1080p scaling.

## Subtitles

- Burn subtitles from the clean base video, not from an already subtitled video.
- Reuse the corrected SRT when iterating subtitle position.
- Default for this user's preferred placement:
  - `--font-size 42`
  - `--bottom-y-ratio 0.92`
  - white text with black stroke and translucent black backing from `burn_subtitles.py`
- If the user says subtitles are too high, move toward `0.92-0.94`; if too low or platform UI may cover them, move back toward `0.84-0.88`.
- Correct recurring ASR terms before burn-in:
  - `进品调研` -> `竞品调研`
  - `sq图` / `SQL图` -> `SKU图`
  - `相亲图` -> `详情图`
  - `封扣` -> `风控`
  - `试验起来` -> `实现起来`

## Cover

- Default cover style: use a real frame from the first 0-5 seconds of the video.
- Do not blur, darken, or recolor the full background unless the user asks.
- Add a centered black rounded rectangle with large white Chinese title text.
- Keep the talking-head/person visible at the lower right.
- Recommended title:
  - line 1: `别再手动存图了`
  - line 2: `商品素材一键入库`
- Output a standalone PNG cover by default.
- Do not prepend the cover to the video unless the user explicitly asks for a cover intro.

## Publish Copy

When preparing publish text, produce two separate platform-ready versions by default:

### 小红书

- Tone: personal, concrete, slightly conversational.
- Structure:
  - title: punchy pain point or outcome, e.g. `别再手动存图了，商品素材一键入库`
  - caption: 2-4 short paragraphs explaining the problem, the workflow, the result, and one takeaway.
  - tags: include 5-8 `#` tags.
- Prefer tags like:
  - `#AI工具`
  - `#效率工具`
  - `#工作流优化`
  - `#插件开发`
  - `#商品素材整理`
  - `#非程序员`
- Avoid overly formal product-copy language.

### 微信视频号

- Tone: restrained, clear, and trustworthy.
- Structure:
  - short title: one concise line, suitable for the platform short-title field.
  - description: 1-3 compact paragraphs.
  - topics: 3-5 topic tags if useful.
- Keep the first sentence direct; say what the tool does and why it matters.
- Avoid excessive hashtags or slang. Prefer fewer, more precise topics.

### Shared content rules

- Mention the concrete workflow when relevant: product page -> plugin collection -> structured product package/system.
- Include the useful reflection when it fits: do competitor research first, then choose the stable implementation path.
- Keep platform copy separate; do not give only one generic version unless the user explicitly asks.

## Cleanup

- Move unwanted generated videos to `~/.Trash` with `safe_cleanup.py`; do not permanently delete.
- Keep original source, current final video, corrected SRT/transcript if useful, and final cover PNG.
