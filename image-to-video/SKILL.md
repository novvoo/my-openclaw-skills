---
name: image-to-video
version: 2.0.0
description: "Convert a static image into a vertical scrolling video. Use when the user wants to turn an image into a video with scrolling/panning effect, e.g. '把这张图做成视频', '图片转视频', '生成滚动视频', 'image to video'. Triggers on: 图片转视频, 图片生成视频, 平移视频, 滚动视频, image to video, pan video, scroll video."
license: MIT
---

# Image to Video Skill

Convert a static image into a vertical scrolling video using PIL + ffmpeg rawvideo pipe.

**Core principle:** PIL scales the image once in memory, then crops each frame pixel-perfectly. Raw frames are piped to ffmpeg for encoding. Zero ffmpeg filters, zero distortion.

## Workflow

### Step 1: Locate the input image

The user may provide an image path, or you may need to find it in `/home/z/my-project/download/`. If the user says "this image" or "这张图", look for the most recent image file in the download directory.

### Step 2: Generate the video

```bash
python3 /home/z/my-project/skills/image-to-video/scripts/image_to_video.py \
  --input "/path/to/input.png" \
  --output "/home/z/my-project/download/{描述性文件名}.mp4" \
  --width 1080 \
  --height 1920 \
  --speed 200 \
  --pause 1.0 \
  --preset ultrafast \
  --crf 23
```

**Parameters:**
- `--width` / `--height`: Output resolution (default: 1080x1920 for vertical video)
- `--speed`: Scroll speed in pixels/sec (default: 100). Higher = faster scroll.
- `--pause`: Pause duration at start/end in seconds (default: 1.0)
- `--ease`: Enable smooth easing (slower start/end). Default is OFF (constant speed).
- `--direction`: `down` (top→bottom) or `up` (bottom→top). Default: `down`.
- `--fps`: Frames per second (default: 30)
- `--crf`: Quality, 18-28, lower = better (default: 23)
- `--preset`: Encoding speed — `ultrafast`, `fast`, `medium`, `slow` (default: `fast`)

**Tips:**
- For tall infographics/reports: `--speed 100` with default settings
- For faster scroll: increase `--speed` to 200-400
- For cinematic feel: add `--ease` for smooth start/stop
- For horizontal video: swap to `--width 1920 --height 1080`
- Duration is auto-calculated from image height and scroll speed

### Step 3: Deliver

Tell the user the video is ready. Keep it brief.

**CRITICAL:**
- Output video must be in `/home/z/my-project/download/` root directory — NO subdirectories
- Use a descriptive Chinese filename, e.g. `浅睡眠研究报告-视频.mp4`
- The video file is the ONLY deliverable
