# Video Channel Polish

一个面向中文录屏口播视频的 Codex Skill，用来把原始演示素材处理成适合小红书和微信视频号发布的成品。

它沉淀了一套固定流程：

```text
原始录屏 -> 去卡壳/压停顿 -> 字幕 -> 封面 -> 双平台发布文案 -> 安全清理
```

## 能做什么

- 分析视频参数、长停顿和口播节奏
- 去掉明显卡壳、重说和长空白
- 轻微提速到更适合短视频发布的语速
- 自动转写中文口播并生成硬字幕
- 修正常见识别错词，例如 `竞品调研`、`SKU 图`、`详情图`
- 从视频前几秒生成黑底白字封面图
- 分别准备小红书和微信视频号发布文案
- 把不需要的中间版本安全移动到 macOS 废纸篓

## 安装

把仓库克隆到 Codex skills 目录：

```bash
git clone https://github.com/wanghaoyu070/video-channel-polish.git \
  ~/.codex/skills/video-channel-polish
```

如果目录已存在，可以进入目录更新：

```bash
cd ~/.codex/skills/video-channel-polish
git pull
```

## 使用方式

在 Codex 中可以这样说：

```text
用 video-channel-polish 处理这段录屏素材
```

或者更具体一点：

```text
用 video-channel-polish 帮我把这个视频剪成适合视频号发布的版本，加字幕、做封面，并准备小红书和微信视频号文案
```

## 默认风格

- 字幕：白字、黑色描边、半透明黑底，位置偏底部
- 字幕默认参数：`font-size 42`，`bottom-y-ratio 0.92`
- 封面：视频前几秒真实画面 + 黑色圆角标题条 + 白色大字
- 默认封面标题：
  - `别再手动存图了`
  - `商品素材一键入库`
- 发布文案：默认输出小红书和微信视频号两套

## 依赖

需要本机可用：

- `ffmpeg`
- `ffprobe`
- Python 3
- Python 包：`Pillow`
- 可选但推荐：`faster_whisper`，用于中文转写

## 目录结构

```text
.
├── SKILL.md
├── agents/
│   └── openai.yaml
├── references/
│   └── style_defaults.md
└── scripts/
    ├── burn_subtitles.py
    ├── clean_speech_video.py
    ├── make_black_title_cover.py
    ├── prepend_cover.py
    ├── safe_cleanup.py
    └── transcribe_subtitle.py
```

## 注意事项

- Skill 会尽量保留原始视频，不覆盖源文件。
- 不需要的生成版本默认移动到 `~/.Trash`，不会直接永久删除。
- 默认只生成封面图，不会把封面强行加到视频开头，除非明确要求。
