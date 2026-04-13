#!/usr/bin/env python3
"""Convert an HTML research report to a high-quality PNG image."""

import sys
import os
from pathlib import Path


def html_to_png(html_path: str, output_path: str, width: int = 800):
    """Render HTML file to PNG using Playwright headless Chromium."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERROR: playwright not installed. Run: pip install playwright && python3 -m playwright install chromium", file=sys.stderr)
        sys.exit(1)

    html_path = os.path.abspath(html_path)
    output_path = os.path.abspath(output_path)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": width, "height": 600},
            device_scale_factor=2,  # 2x for retina quality
        )
        page.goto(f"file://{html_path}", wait_until="networkidle")

        # Auto-fit height to content
        height = page.evaluate("document.documentElement.scrollHeight")
        page.set_viewport_size({"width": width, "height": height})

        page.screenshot(path=output_path, full_page=True)
        browser.close()

    print(f"PNG saved to {output_path}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Convert HTML report to PNG")
    parser.add_argument("--input", required=True, help="Path to HTML file")
    parser.add_argument("--output", required=True, help="Output PNG path")
    parser.add_argument("--width", type=int, default=800, help="Viewport width (default: 800)")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"ERROR: {args.input} not found", file=sys.stderr)
        sys.exit(1)

    html_to_png(args.input, args.output, width=args.width)


if __name__ == "__main__":
    main()
