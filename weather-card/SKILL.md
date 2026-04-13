---
name: weather-card
version: 1.1.0
description: Generate a beautiful SVG weather card for any city, then convert to PNG. Use when the user asks about weather, e.g. "今天北京天气怎么样", "上海天气", "weather in Tokyo", "查天气". Triggers on any weather-related query mentioning a location.
license: MIT
---

# Weather Card Skill

Generate a polished weather card (PNG) for any location using real-time weather data.

## Workflow

### Step 1: Get Weather Data

Use `web_search` to fetch current weather for the requested location. Search queries like:

- `"北京 今天天气 实时温度"`
- `"Shanghai weather today temperature"`
- `"广州 天气 湿度 风速"`

Extract these fields from search results:
- **city**: City name (use user's wording)
- **temp**: Current temperature (e.g. "24")
- **condition**: Weather condition in Chinese (晴/多云/阴/小雨/中雨/大雨/暴雨/雷阵雨/雪/雾)
- **high**: Today's high temperature
- **low**: Today's low temperature
- **humidity**: Humidity percentage (e.g. "62%")
- **wind**: Wind speed (e.g. "12km/h")
- **uv**: UV index level (低/中等/高/很强)

If some fields are missing, use reasonable defaults but try to fill the core ones (temp, condition, high, low).

### Step 2: Generate Card

Run the script — it outputs PNG directly (SVG is handled internally as a temp file):

```bash
python3 /home/z/my-project/skills/weather-card/scripts/weather_card.py \
  --city "北京" \
  --temp "24" \
  --condition "多云" \
  --high "27" \
  --low "18" \
  --humidity "62%" \
  --wind "12km/h" \
  --uv "中等" \
  --output /home/z/my-project/download/weather-北京.png
```

Only one file is produced: the PNG card. No SVG clutter.

### Step 3: Deliver

Tell the user the card is ready. Keep it brief — the card speaks for itself.

## Supported Conditions

| Condition | Visual |
|-----------|--------|
| 晴 | Sun with rays |
| 多云 | Sun + cloud |
| 阴 | Cloud only |
| 小雨/中雨/大雨/暴雨 | Cloud + rain (varying intensity) |
| 雷阵雨 | Dark cloud + heavy rain + lightning |
| 雪 | Cloud + snowflakes |
| 雾 | Horizontal fog lines |

Each condition has its own color theme.

## Notes

- Always save to `/home/z/my-project/download/`
- Output is 2x resolution (800x1080) for crisp display
- If web_search fails to return weather data, say so clearly — don't fabricate
- The date in the card is auto-generated from current time
- For English-speaking users, keep the card in English; for Chinese users, keep it in Chinese
