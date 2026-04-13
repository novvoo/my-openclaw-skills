#!/usr/bin/env python3
"""Generate a polished HTML research report from findings data."""

import json
import sys
import re
from datetime import datetime
from pathlib import Path


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^\w\s\u4e00-\u9fff-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    return text[:60]


def escape_html(text: str) -> str:
    return (text.replace('&', '&amp;').replace('<', '&lt;')
            .replace('>', '&gt;').replace('"', '&quot;'))


def generate_report(data: dict, lang: str = "zh") -> str:
    question = data["question"]
    findings_by_subq = data.get("findings_by_subq", {})
    all_findings = data.get("all_findings", [])
    sources = data.get("sources", [])
    gaps = data.get("gaps", [])
    stats = data.get("stats", {})
    sub_questions = data.get("sub_questions", [])
    rounds = data.get("rounds", 0)

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Detect language
    has_chinese = any('\u4e00' <= c <= '\u9fff' for c in question)
    if lang == "auto":
        lang = "zh" if has_chinese else "en"

    # Chinese numbering
    cn_nums = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十",
               "十一", "十二", "十三", "十四", "十五"]

    # Build TOC
    toc_items = []
    for i, sq in enumerate(sub_questions):
        sq_findings = findings_by_subq.get(sq, [])
        if not sq_findings:
            continue
        num = cn_nums[i] if lang == "zh" else str(i + 1)
        sid = slugify(sq)
        toc_items.append(f'<li><a href="#{sid}">{num}、{escape_html(sq)}</a></li>')

    toc_html = "\n".join(toc_items) if toc_items else "<p>暂无内容</p>"

    # Build sections
    sections = []
    for i, sq in enumerate(sub_questions):
        sq_findings = findings_by_subq.get(sq, [])
        if not sq_findings:
            continue
        sid = slugify(sq)
        num = cn_nums[i] if lang == "zh" else str(i + 1)

        # Sort: high relevance first
        sq_findings.sort(key=lambda f: 0 if f["relevance"] == "high" else 1)

        findings_html = []
        for f in sq_findings:
            source_tag = ""
            if f.get("source_url"):
                source_tag = f'<span class="source">来源: <a href="{escape_html(f["source_url"])}" target="_blank">{escape_html(f.get("source_name", f["source_url"]))}</a></span>'
            elif f.get("source_name"):
                source_tag = f'<span class="source">来源: {escape_html(f["source_name"])}</span>'

            type_label = {"fact": "事实", "opinion": "观点", "data": "数据", "perspective": "视角"}.get(f.get("type", "fact"), f.get("type", ""))
            if lang == "en":
                type_label = {"fact": "Fact", "opinion": "Opinion", "data": "Data", "perspective": "Perspective"}.get(f.get("type", "fact"), f.get("type", ""))

            findings_html.append(f"""
            <div class="finding">
              <div class="finding-content">{escape_html(f['content'])}</div>
              <div class="finding-meta">
                <span class="type-tag">{escape_html(type_label)}</span>
                {source_tag}
              </div>
            </div>""")

        section_html = f"""
    <section id="{sid}">
      <h2>{num}、{escape_html(sq)}</h2>
      <div class="findings-list">
        {''.join(findings_html)}
      </div>
    </section>"""
        sections.append(section_html)

    sections_html = "\n".join(sections)

    # Build sources list
    sources_html = ""
    if sources:
        src_items = []
        for i, s in enumerate(sorted(sources, key=lambda x: -x["cited_count"]), 1):
            src_items.append(f'<li>[{i}] <a href="{escape_html(s["url"])}" target="_blank">{escape_html(s["name"])}</a> <span class="cite-count">(引用 {s["cited_count"]} 次)</span></li>')
        sources_html = f"""
    <section id="references">
      <h2>参考文献</h2>
      <ol class="references-list">
        {''.join(src_items)}
      </ol>
    </section>"""

    # Build gaps section
    gaps_html = ""
    unresolved = [g for g in gaps if not g.get("resolved", False)]
    if unresolved:
        gap_items = [f'<li class="gap-item gap-{g.get("priority", "medium")}">{escape_html(g["description"])}</li>' for g in unresolved]
        gaps_html = f"""
    <section id="gaps">
      <h2>研究局限</h2>
      <p>以下信息在本次研究中未能充分覆盖：</p>
      <ul class="gaps-list">
        {''.join(gap_items)}
      </ul>
    </section>"""

    # Summary stats
    stats_text = f"经过 {rounds} 轮搜索，共收集 {stats.get('total_findings', 0)} 条发现，引用 {stats.get('sources', 0)} 个来源。" if lang == "zh" else f"After {rounds} rounds of search, collected {stats.get('total_findings', 0)} findings from {stats.get('sources', 0)} sources."

    html = f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape_html(question)}</title>
  <style>
    :root {{
      --bg: #FFFFFF;
      --text: #212529;
      --primary: #0D6EFD;
      --primary-light: #e7f1ff;
      --border: #dee2e6;
      --muted: #6c757d;
      --surface: #f8f9fa;
    }}
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      font-family: "Alibaba PuHuiTi 3.0", "Noto Sans SC", "Noto Serif SC", -apple-system, sans-serif;
      background: var(--bg);
      color: var(--text);
      font-size: 16px;
      line-height: 1.8;
    }}
    .container {{
      max-width: 800px;
      margin: 0 auto;
      padding: 40px 24px 80px;
    }}
    h1 {{
      font-size: 28px;
      text-align: center;
      margin-bottom: 8px;
      font-weight: 700;
    }}
    .meta {{
      text-align: center;
      color: var(--muted);
      font-size: 13px;
      margin-bottom: 32px;
    }}
    .toc {{
      background: var(--surface);
      border-radius: 12px;
      padding: 20px 28px;
      margin-bottom: 36px;
    }}
    .toc h3 {{
      font-size: 15px;
      color: var(--muted);
      margin-bottom: 12px;
      font-weight: 500;
    }}
    .toc ul {{
      list-style: none;
      padding: 0;
    }}
    .toc li {{
      margin-bottom: 6px;
    }}
    .toc a {{
      color: var(--primary);
      text-decoration: none;
      font-size: 15px;
    }}
    .toc a:hover {{
      text-decoration: underline;
    }}
    h2 {{
      font-size: 22px;
      margin-top: 40px;
      margin-bottom: 20px;
      padding-bottom: 0.4em;
      border-bottom: 1px solid var(--border);
      font-weight: 600;
    }}
    .finding {{
      background: var(--surface);
      border-radius: 10px;
      padding: 16px 20px;
      margin-bottom: 12px;
      border-left: 3px solid var(--primary);
    }}
    .finding-content {{
      font-size: 15px;
      line-height: 1.75;
      margin-bottom: 8px;
    }}
    .finding-meta {{
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 12px;
      color: var(--muted);
    }}
    .type-tag {{
      background: var(--primary-light);
      color: var(--primary);
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 11px;
      font-weight: 500;
    }}
    .source a {{
      color: var(--primary);
      text-decoration: none;
    }}
    .source a:hover {{
      text-decoration: underline;
    }}
    .references-list {{
      padding-left: 24px;
    }}
    .references-list li {{
      margin-bottom: 8px;
      font-size: 14px;
      color: var(--muted);
    }}
    .references-list a {{
      color: var(--primary);
    }}
    .cite-count {{
      font-size: 12px;
      opacity: 0.7;
    }}
    .gaps-list {{
      padding-left: 20px;
    }}
    .gap-item {{
      margin-bottom: 6px;
      font-size: 14px;
      color: var(--muted);
    }}
    .gap-high {{ color: #dc3545; }}
    .gap-medium {{ color: #fd7e14; }}
    .gap-low {{ color: #198754; }}
    .stats-bar {{
      text-align: center;
      color: var(--muted);
      font-size: 13px;
      margin-bottom: 24px;
      padding: 12px;
      background: var(--surface);
      border-radius: 8px;
    }}
  </style>
</head>
<body>
  <div class="container">
    <h1>{escape_html(question)}</h1>
    <div class="meta">Deep Research Report · {now}</div>

    <div class="stats-bar">{stats_text}</div>

    <nav class="toc">
      <h3>目录</h3>
      <ul>{toc_html}</ul>
    </nav>

    {sections_html}
    {sources_html}
    {gaps_html}
  </div>
</body>
</html>"""
    return html


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate HTML research report")
    parser.add_argument("--input", required=True, help="Path to findings export JSON")
    parser.add_argument("--output", required=True, help="Output HTML path")
    parser.add_argument("--lang", default="auto", choices=["zh", "en", "auto"])
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    html = generate_report(data, lang=args.lang)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Report saved to {args.output}")


if __name__ == "__main__":
    main()
