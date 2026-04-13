#!/usr/bin/env python3
"""Generate a weather card PNG from command-line parameters."""

import argparse
import math
import os
import sys
import tempfile
import datetime

try:
    import cairosvg
except ImportError:
    print("ERROR: cairosvg not installed. Run: pip install cairosvg", file=sys.stderr)
    sys.exit(1)

CONDITIONS = {
    "晴":     {"sun": True,  "cloud": False, "rain": False, "snow": False, "lightning": False, "fog": False},
    "多云":   {"sun": True,  "cloud": True,  "rain": False, "snow": False, "lightning": False, "fog": False},
    "阴":     {"sun": False, "cloud": True,  "rain": False, "snow": False, "lightning": False, "fog": False},
    "小雨":   {"sun": False, "cloud": True,  "rain": "light",  "snow": False, "lightning": False, "fog": False},
    "中雨":   {"sun": False, "cloud": True,  "rain": "medium", "snow": False, "lightning": False, "fog": False},
    "大雨":   {"sun": False, "cloud": True,  "rain": "heavy",  "snow": False, "lightning": False, "fog": False},
    "暴雨":   {"sun": False, "cloud": True,  "rain": "heavy",  "snow": False, "lightning": False, "fog": False},
    "雷阵雨": {"sun": False, "cloud": True,  "rain": "heavy",  "snow": False, "lightning": True,  "fog": False},
    "雪":     {"sun": False, "cloud": True,  "rain": False, "snow": True,  "lightning": False, "fog": False},
    "雾":     {"sun": False, "cloud": False, "rain": False, "snow": False, "lightning": False, "fog": True},
}

THEMES = {
    "晴":     ("#4facfe", "#00f2fe"),
    "多云":   ("#667eea", "#764ba2"),
    "阴":     ("#8e9eab", "#c4cdd5"),
    "小雨":   ("#616161", "#9bc5c3"),
    "中雨":   ("#4b6584", "#9bc5c3"),
    "大雨":   ("#373B44", "#4286f4"),
    "暴雨":   ("#2c3e50", "#4286f4"),
    "雷阵雨": ("#0f0c29", "#302b63"),
    "雪":     ("#a8c0d6", "#6b8fa3"),
    "雾":     ("#bdc3c7", "#95a5a6"),
}

FONT = "'Microsoft YaHei', 'SimHei', 'Noto Sans CJK SC', sans-serif"

CARD_X, CARD_Y = 16, 16
CARD_W, CARD_H = 368, 508
CARD_R = 24
LOC_Y = 62
DATE_Y = 84
ICON_CX = 200
ICON_CY = 200
TEMP_Y = 340
COND_Y = 374
DETAIL_Y = 418
DETAIL_LABEL_Y = 0
DETAIL_VALUE_Y = 26
HILO_Y = 478


def _match(key_map, condition, default):
    if condition in key_map:
        return key_map[condition]
    for key, val in key_map.items():
        if key in condition or condition in key:
            return val
    return key_map[default]


def _esc(text):
    return (str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))


def _sun_svg(cx, cy):
    parts = [
        f'<circle cx="{cx}" cy="{cy}" r="65" fill="#FFE066" opacity="0.18"/>',
        f'<circle cx="{cx}" cy="{cy}" r="36" fill="#FFE066" opacity="0.95"/>',
    ]
    for i in range(8):
        a = math.radians(i * 45)
        x1 = cx + 46 * math.cos(a)
        y1 = cy + 46 * math.sin(a)
        x2 = cx + 60 * math.cos(a)
        y2 = cy + 60 * math.sin(a)
        parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#FFE066" stroke-width="3" stroke-linecap="round" opacity="0.65"/>')
    return "\n".join(parts)


def _cloud_svg(cx, cy, dark=False):
    fill = "#c8cdd3" if dark else "#ffffff"
    opacity = "0.92" if dark else "0.95"
    return (f'<g opacity="{opacity}">'
            f'<ellipse cx="{cx}" cy="{cy}" rx="52" ry="28" fill="{fill}"/>'
            f'<ellipse cx="{cx-32}" cy="{cy+10}" rx="36" ry="24" fill="{fill}"/>'
            f'<ellipse cx="{cx+32}" cy="{cy+10}" rx="36" ry="24" fill="{fill}"/>'
            f'<ellipse cx="{cx}" cy="{cy+18}" rx="56" ry="18" fill="{fill}"/>'
            f'</g>')


def _rain_svg(cx, cy, intensity):
    cfg = {"light": (5, 10, 16), "medium": (7, 8, 22), "heavy": (9, 6, 28)}
    count, spacing, length = cfg.get(intensity, cfg["medium"])
    x_start = cx - (count - 1) * spacing // 2
    parts = []
    for i in range(count):
        x = x_start + i * spacing
        parts.append(f'<line x1="{x}" y1="{cy}" x2="{x-3}" y2="{cy+length}" stroke="white" stroke-width="1.8" stroke-linecap="round" opacity="0.55"/>')
    return "\n".join(parts)


def _lightning_svg(cx, cy):
    return (f'<polygon points="{cx+5},{cy} {cx-5},{cy+25} {cx+3},{cy+25} '
            f'{cx-7},{cy+50} {cx+15},{cy+20} {cx+7},{cy+20} {cx+17},{cy}" '
            f'fill="#FBBF24" opacity="0.9"/>')


def _snow_svg(cx, cy):
    parts = []
    positions = [(cx-28, cy+5), (cx-8, cy+15), (cx+12, cy+3), (cx+30, cy+18), (cx-18, cy+30), (cx+5, cy+35)]
    for sx, sy in positions:
        parts.append(f'<circle cx="{sx}" cy="{sy}" r="2.5" fill="white" opacity="0.85"/>')
        for j in range(6):
            a = math.radians(j * 60)
            parts.append(f'<line x1="{sx+3*math.cos(a):.1f}" y1="{sy+3*math.sin(a):.1f}" x2="{sx+6*math.cos(a):.1f}" y2="{sy+6*math.sin(a):.1f}" stroke="white" stroke-width="1" opacity="0.55"/>')
    return "\n".join(parts)


def _fog_svg(cx, cy):
    parts = []
    for i in range(5):
        y = cy + i * 16
        w = 110 - i * 8
        op = max(0.15, 0.3 - i * 0.03)
        parts.append(f'<line x1="{cx-w}" y1="{y}" x2="{cx+w}" y2="{y}" stroke="white" stroke-width="3.5" stroke-linecap="round" opacity="{op}"/>')
    return "\n".join(parts)


def _build_icon(cfg, cx, cy):
    parts = []
    if cfg["sun"]:
        parts.append(_sun_svg(cx - 20, cy - 10))
    if cfg["cloud"]:
        dark = cfg["rain"] == "heavy" or cfg["lightning"]
        cloud_cx = cx + 10 if cfg["sun"] else cx
        parts.append(_cloud_svg(cloud_cx, cy, dark=dark))
        rain_start_y = cy + 50
    else:
        rain_start_y = cy + 30
    if cfg["rain"]:
        parts.append(_rain_svg(cx, rain_start_y, cfg["rain"]))
    if cfg["lightning"]:
        parts.append(_lightning_svg(cx - 5, rain_start_y + 5))
    if cfg["snow"]:
        parts.append(_snow_svg(cx, cy + 45))
    if cfg["fog"]:
        parts.append(_fog_svg(cx, cy - 20))
    return "\n".join(parts)


def _humidity_icon():
    return ('<path d="M-3,-5 Q0,-10 3,-5" stroke="white" stroke-width="1.3" fill="none" opacity="0.6"/>'
            '<ellipse cx="0" cy="2" rx="5" ry="3.5" fill="none" stroke="white" stroke-width="1.3" opacity="0.6"/>')

def _wind_icon():
    return ('<path d="M-8,-3 Q0,-7 8,-3" stroke="white" stroke-width="1.5" fill="none" stroke-linecap="round" opacity="0.6"/>'
            '<path d="M-6,2 Q2,-2 10,2" stroke="white" stroke-width="1.5" fill="none" stroke-linecap="round" opacity="0.6"/>'
            '<path d="M-4,7 Q4,3 8,7" stroke="white" stroke-width="1.5" fill="none" stroke-linecap="round" opacity="0.6"/>')

def _uv_icon():
    return ('<circle cx="0" cy="0" r="4" fill="#FBBF24" opacity="0.75"/>'
            '<line x1="0" y1="-7" x2="0" y2="-10" stroke="#FBBF24" stroke-width="1.2" opacity="0.6"/>'
            '<line x1="5" y1="-5" x2="7" y2="-7" stroke="#FBBF24" stroke-width="1.2" opacity="0.6"/>'
            '<line x1="-5" y1="-5" x2="-7" y2="-7" stroke="#FBBF24" stroke-width="1.2" opacity="0.6"/>'
            '<line x1="7" y1="0" x2="10" y2="0" stroke="#FBBF24" stroke-width="1.2" opacity="0.6"/>'
            '<line x1="-7" y1="0" x2="-10" y2="0" stroke="#FBBF24" stroke-width="1.2" opacity="0.6"/>')


def generate_svg(city, temp, condition, high, low, humidity, wind, uv, date_str=None):
    cfg = _match(CONDITIONS, condition, "多云")
    c1, c2 = _match(THEMES, condition, "多云")
    if date_str is None:
        date_str = datetime.datetime.now().strftime("%Y年%m月%d日")
    icon_svg = _build_icon(cfg, ICON_CX, ICON_CY)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 540" width="400" height="540">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{c1}"/>
      <stop offset="100%" stop-color="{c2}"/>
    </linearGradient>
    <filter id="shadow" x="-8%" y="-4%" width="116%" height="112%">
      <feDropShadow dx="0" dy="6" stdDeviation="14" flood-color="#000" flood-opacity="0.22"/>
    </filter>
  </defs>
  <rect x="{CARD_X}" y="{CARD_Y}" width="{CARD_W}" height="{CARD_H}" rx="{CARD_R}" fill="url(#bg)" filter="url(#shadow)"/>
  <circle cx="350" cy="55" r="70" fill="white" opacity="0.05"/>
  <circle cx="55" cy="490" r="50" fill="white" opacity="0.04"/>
  <text x="52" y="{LOC_Y}" font-family="{FONT}" font-size="17" fill="white" opacity="0.9">{_esc(city)}</text>
  <text x="52" y="{DATE_Y}" font-family="{FONT}" font-size="12" fill="white" opacity="0.5">{_esc(date_str)}</text>
  {icon_svg}
  <text x="52" y="{TEMP_Y}" font-family="{FONT}" font-size="68" fill="white" font-weight="300">{_esc(temp)}°</text>
  <text x="52" y="{COND_Y}" font-family="{FONT}" font-size="17" fill="white" opacity="0.7">{_esc(condition)}</text>
  <line x1="52" y1="392" x2="348" y2="392" stroke="white" stroke-width="0.5" opacity="0.15"/>
  <g transform="translate(100, {DETAIL_Y})">
    <g transform="translate(0, -14)">{_humidity_icon()}</g>
    <text x="0" y="{DETAIL_LABEL_Y}" font-family="{FONT}" font-size="11" fill="white" text-anchor="middle" opacity="0.45">湿度</text>
    <text x="0" y="{DETAIL_VALUE_Y}" font-family="{FONT}" font-size="18" fill="white" text-anchor="middle" font-weight="500">{_esc(humidity)}</text>
  </g>
  <g transform="translate(200, {DETAIL_Y})">
    <g transform="translate(0, -14)">{_wind_icon()}</g>
    <text x="0" y="{DETAIL_LABEL_Y}" font-family="{FONT}" font-size="11" fill="white" text-anchor="middle" opacity="0.45">风速</text>
    <text x="0" y="{DETAIL_VALUE_Y}" font-family="{FONT}" font-size="18" fill="white" text-anchor="middle" font-weight="500">{_esc(wind)}</text>
  </g>
  <g transform="translate(300, {DETAIL_Y})">
    <g transform="translate(0, -14)">{_uv_icon()}</g>
    <text x="0" y="{DETAIL_LABEL_Y}" font-family="{FONT}" font-size="11" fill="white" text-anchor="middle" opacity="0.45">紫外线</text>
    <text x="0" y="{DETAIL_VALUE_Y}" font-family="{FONT}" font-size="18" fill="white" text-anchor="middle" font-weight="500">{_esc(uv)}</text>
  </g>
  <text x="52" y="{HILO_Y}" font-family="{FONT}" font-size="13" fill="white" opacity="0.5">
    <tspan>↑ 最高 {_esc(high)}°</tspan>
    <tspan dx="24">↓ 最低 {_esc(low)}°</tspan>
  </text>
</svg>"""
    return svg


def main():
    parser = argparse.ArgumentParser(description="Generate weather card PNG")
    parser.add_argument("--city", required=True)
    parser.add_argument("--temp", required=True)
    parser.add_argument("--condition", default="多云")
    parser.add_argument("--high", default="--")
    parser.add_argument("--low", default="--")
    parser.add_argument("--humidity", default="--")
    parser.add_argument("--wind", default="--")
    parser.add_argument("--uv", default="--")
    parser.add_argument("--date", default=None)
    parser.add_argument("--output", required=True, help="Output PNG path")
    args = parser.parse_args()

    svg = generate_svg(
        city=args.city, temp=args.temp, condition=args.condition,
        high=args.high, low=args.low, humidity=args.humidity,
        wind=args.wind, uv=args.uv, date_str=args.date,
    )

    fd, svg_path = tempfile.mkstemp(suffix=".svg")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(svg)
        cairosvg.svg2png(url=svg_path, write_to=args.output, scale=2)
        print(f"PNG saved to {args.output}")
    finally:
        if os.path.exists(svg_path):
            os.unlink(svg_path)


if __name__ == "__main__":
    main()
