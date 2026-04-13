#!/usr/bin/env python3
"""Convert an HTML research report to PDF using Playwright headless Chromium."""

import sys
import os


def html_to_pdf(html_path: str, output_path: str, width: str = "210mm"):
    """Render HTML file to PDF using Playwright."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERROR: playwright not installed. Run: pip install playwright && python3 -m playwright install chromium", file=sys.stderr)
        sys.exit(1)

    html_path = os.path.abspath(html_path)
    output_path = os.path.abspath(output_path)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(f"file://{html_path}", wait_until="networkidle")

        page.pdf(
            path=output_path,
            width=width,
            margin={"top": "15mm", "bottom": "15mm", "left": "12mm", "right": "12mm"},
            print_background=True,
            display_header_footer=False,
        )
        browser.close()

    print(f"PDF saved to {output_path}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Convert HTML report to PDF")
    parser.add_argument("--input", required=True, help="Path to HTML file")
    parser.add_argument("--output", required=True, help="Output PDF path")
    parser.add_argument("--width", default="210mm", help="Page width (default: 210mm = A4)")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"ERROR: {args.input} not found", file=sys.stderr)
        sys.exit(1)

    html_to_pdf(args.input, args.output, width=args.width)


if __name__ == "__main__":
    main()
