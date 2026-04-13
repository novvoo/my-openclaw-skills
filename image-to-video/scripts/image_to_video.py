#!/usr/bin/env python3
"""Generate a vertical scrolling video from a static image.

Uses PIL for in-memory scaling/cropping + pipes raw frames to ffmpeg.
Pure pixel crop — zero scaling, zero distortion.
"""

import argparse
import math
import os
import subprocess
import sys
from PIL import Image


def create_panning_video(
    image_path: str,
    output_path: str,
    duration: float = 8.0,
    fps: int = 30,
    speed_px_per_sec: float = 100,
    direction: str = "down",
    video_width: int = 1080,
    video_height: int = 1920,
    crf: int = 23,
    preset: str = "fast",
    pause_sec: float = 1.0,
    ease: bool = False,
):
    """
    Create a vertical scrolling video from a tall image.

    1. PIL scales image to video_width, preserving aspect ratio (LANCZOS)
    2. For each frame, crop viewport from in-memory image
    3. Pipe raw RGB frames to ffmpeg via stdin
    """
    img = Image.open(image_path).convert("RGB")

    # Scale to video_width, preserve aspect ratio
    scale = video_width / img.width
    scaled_h = int(img.height * scale)
    scaled_h = scaled_h if scaled_h % 2 == 0 else scaled_h + 1

    print(f"Input:  {img.width}x{img.height}")
    print(f"Scale:  {video_width}x{scaled_h}")
    print(f"Output: {video_width}x{video_height}")

    img = img.resize((video_width, scaled_h), Image.LANCZOS)
    print(f"Memory: {img.width * img.height * 3 / 1024**2:.1f} MB")

    if scaled_h <= video_height:
        # Image shorter than viewport — static video
        scroll_dist = 0
        scroll_dur = 0.0
        total_dur = pause_sec * 2 + 3.0
    else:
        scroll_dist = scaled_h - video_height
        scroll_dur = scroll_dist / speed_px_per_sec
        total_dur = scroll_dur + pause_sec * 2

    total_frames = int(total_dur * fps)
    print(f"Frames: {total_frames}, Duration: {total_dur:.1f}s, Scroll: {scroll_dist}px")

    def get_y(t: float) -> int:
        """Return crop y-position based on time, with optional easing."""
        if scroll_dist == 0:
            return 0
        if t <= pause_sec:
            return 0
        if t >= pause_sec + scroll_dur:
            return scroll_dist
        progress = (t - pause_sec) / scroll_dur
        if ease:
            y = scroll_dist * (1 - math.cos(math.pi * progress)) / 2
        else:
            y = scroll_dist * progress
        return int(y)

    # Launch ffmpeg, read raw video from stdin
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-pixel_format", "rgb24",
        "-video_size", f"{video_width}x{video_height}",
        "-framerate", str(fps),
        "-i", "pipe:0",
        "-c:v", "libx264",
        "-preset", preset,
        "-crf", str(crf),
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output_path,
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    try:
        for frame_idx in range(total_frames):
            t = frame_idx / fps
            y = get_y(t)
            tile = img.crop((0, y, video_width, y + video_height))
            proc.stdin.write(tile.tobytes())

            if frame_idx % fps == 0:
                pct = frame_idx / total_frames * 100
                print(f"\r  Progress: {frame_idx}/{total_frames} ({pct:.0f}%)", end="", flush=True)

        proc.stdin.close()
        proc.wait()

        if proc.returncode != 0:
            print(f"\nERROR: ffmpeg exited with code {proc.returncode}", file=sys.stderr)
            sys.exit(1)

        file_size = os.path.getsize(output_path)
        print(f"\nVideo saved to {output_path} ({file_size / 1024:.0f}KB, {total_dur:.1f}s)")

    except BrokenPipeError:
        print("\nERROR: ffmpeg pipe broken", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Convert image to vertical scrolling video")
    parser.add_argument("--input", required=True, help="Input image path")
    parser.add_argument("--output", required=True, help="Output video path (.mp4)")
    parser.add_argument("--duration", type=float, default=8.0, help="Approx duration in seconds (default: 8)")
    parser.add_argument("--fps", type=int, default=30, help="Frames per second (default: 30)")
    parser.add_argument("--speed", type=float, default=100, help="Scroll speed in px/sec (default: 100)")
    parser.add_argument("--direction", default="down", choices=["up", "down"],
                        help="Pan direction (default: down)")
    parser.add_argument("--width", type=int, default=1080, help="Output video width (default: 1080)")
    parser.add_argument("--height", type=int, default=1920, help="Output video height (default: 1920)")
    parser.add_argument("--crf", type=int, default=23, help="Quality 18-28, lower=better (default: 23)")
    parser.add_argument("--preset", default="fast",
                        choices=["ultrafast", "fast", "medium", "slow"],
                        help="Encoding speed (default: fast)")
    parser.add_argument("--pause", type=float, default=1.0, help="Pause at start/end in seconds (default: 1.0)")
    parser.add_argument("--ease", action="store_true", help="Enable smooth easing (slower start/end)")
    args = parser.parse_args()

    create_panning_video(
        image_path=args.input,
        output_path=args.output,
        duration=args.duration,
        fps=args.fps,
        speed_px_per_sec=args.speed,
        direction=args.direction,
        video_width=args.width,
        video_height=args.height,
        crf=args.crf,
        preset=args.preset,
        pause_sec=args.pause,
        ease=args.ease,
    )


if __name__ == "__main__":
    main()
