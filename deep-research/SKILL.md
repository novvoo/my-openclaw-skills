---
name: deep-research
version: 1.1.0
description: "Deep research agent for systematic, multi-round investigation of complex questions. Use when the user asks to 'research', 'deep dive', 'investigate', 'look into', or any question requiring thorough multi-source analysis beyond a simple search. Produces a structured HTML report with citations, then converts to PNG for delivery. Triggers on: 深度研究, deep research, 调查一下, 帮我研究, 详细分析."
license: MIT
---

# Deep Research Skill

A systematic research agent that decomposes questions, searches iteratively, persists findings, and generates cited HTML reports.

## Architecture

```
skills/deep-research/
├── SKILL.md                    # This file
└── scripts/
    ├── findings.py             # Findings persistence (add/query/export)
    ├── report.py               # HTML report generator
    ├── html_to_png.py          # HTML → PNG converter (Playwright)
    └── html_to_pdf.py          # HTML → PDF converter (Playwright)
```

## Workflow

### Phase 1: Decompose (Round 0)

When the user asks a research question:

1. **Understand the real question.** What are they actually trying to decide or understand? The surface question often hides a deeper one.
2. **Decompose into 3-7 sub-questions.** Each sub-question should be independently searchable and collectively cover the full scope.
3. **Initialize the research workspace:**

```bash
python3 /home/z/my-project/skills/deep-research/scripts/findings.py init \
  --workspace "/home/z/my-project/download/research-{slug}" \
  --question "原始问题" \
  --sub-questions "子问题1" "子问题2" "子问题3"
```

Where `{slug}` is a short identifier (e.g., `ai-safety-2026`).

### Phase 2: Research Loop (Rounds 1-N)

For each round, follow this cycle:

#### 2a. Plan the round

Before searching, state:
- Which sub-question(s) to focus on this round
- What specific search queries to use
- What information gaps you're trying to fill

#### 2b. Execute searches

Use `web_search` to find sources. For each search:
- Use specific, targeted queries (not vague ones)
- If Chinese topic, search in Chinese; if international, search in both languages
- 3-5 searches per round is typical

#### 2c. Deep read promising sources

Use `web-reader` to extract full content from the most relevant URLs. Don't just rely on snippets.

#### 2d. Save findings

For each significant finding, save it:

```bash
python3 /home/z/my-project/skills/deep-research/scripts/findings.py add \
  --workspace "/home/z/my-project/download/research-{slug}" \
  --sub-question "对应的子问题" \
  --content "发现的具体内容" \
  --url "https://source-url.com" \
  --source "来源名称" \
  --relevance "high|medium|low" \
  --type "fact|opinion|data|perspective" \
  --key-data "关键数据点（可选）"
```

**Finding types:**
- `fact` — Verifiable factual claim
- `opinion` — Expert or institutional viewpoint
- `data` — Statistics, numbers, measurements
- `perspective` — Alternative framing or angle

#### 2e. Record gaps

When you notice missing information:

```bash
python3 /home/z/my-project/skills/deep-research/scripts/findings.py gap \
  --workspace "/home/z/my-project/download/research-{slug}" \
  --description "缺失的具体信息" \
  --priority "high|medium|low"
```

#### 2f. Evaluate completeness

After each round, check stats:

```bash
python3 /home/z/my-project/skills/deep-research/scripts/findings.py stats \
  --workspace "/home/z/my-project/download/research-{slug}"
```

**Continue to next round if ANY of these are true:**
- High-priority gaps remain unresolved
- Some sub-questions have zero or only low-relevance findings
- You've found contradictory information that needs more sources to resolve
- The user's implicit deeper question hasn't been addressed

**Stop when:**
- All sub-questions have at least 2-3 high-relevance findings
- No high-priority gaps remain
- Additional rounds are yielding diminishing returns
- You've reached 8 rounds (hard limit — synthesize what you have)

### Phase 3: Synthesize & Report

#### 3a. Export findings

```bash
python3 /home/z/my-project/skills/deep-research/scripts/findings.py export \
  --workspace "/home/z/my-project/download/research-{slug}" \
  --output "/home/z/my-project/download/research-{slug}/export.json"
```

#### 3b. Generate HTML report (intermediate file)

```bash
python3 /home/z/my-project/skills/deep-research/scripts/report.py \
  --input "/home/z/my-project/download/research-{slug}/export.json" \
  --output "/tmp/research-{slug}.html" \
  --lang "zh"
```

**Note:** HTML is an intermediate file. Save to `/tmp/`, NOT to the download directory. The user should never see this file.

#### 3c. Enhance the report (optional but recommended)

Read the generated HTML, then use your judgment to enhance it:
- Add a **summary/executive summary** section at the top
- Add **analysis/synthesis** paragraphs that connect findings across sub-questions
- Highlight **contradictions** between sources
- Add **conclusions** with your assessment
- If there are data points, consider adding Chart.js visualizations

The raw report is a good skeleton. Your synthesis makes it a real research report.

#### 3d. Convert to PNG

Use Playwright to render the final HTML report as a high-quality PNG image:

```bash
python3 /home/z/my-project/skills/deep-research/scripts/html_to_png.py \
  --input "/tmp/research-{slug}.html" \
  --output "/home/z/my-project/download/{研究主题}-研究报告.png" \
  --width 800
```

This produces a 2x resolution (1600px wide) PNG.

#### 3e. Convert to PDF

Use Playwright to render the same HTML report as a PDF:

```bash
python3 /home/z/my-project/skills/deep-research/scripts/html_to_pdf.py \
  --input "/tmp/research-{slug}.html" \
  --output "/home/z/my-project/download/{研究主题}-研究报告.pdf"
```

This produces an A4-width PDF with print background enabled.

**CRITICAL: Both PNG and PDF filenames must be placed directly in `/home/z/my-project/download/` root directory, NOT in a subdirectory.** Use descriptive Chinese filenames like `浅睡眠成因-研究报告.png` and `浅睡眠成因-研究报告.pdf`. Files in subdirectories will NOT be delivered to the user.

**After successful conversion, delete the intermediate HTML:**
```bash
rm -f /tmp/research-{slug}.html
```

**Critical rules:**
- PNG and PDF are the deliverables to the user
- Both must be in `/home/z/my-project/download/` root — NO subdirectories
- Use descriptive Chinese filenames for both files
- HTML is a temporary intermediate file — save to `/tmp/`, delete after conversion
- Do NOT mention HTML in your response to the user
- Do NOT save HTML to `/home/z/my-project/download/`

#### 3f. Deliver

Tell the user:
- What the research covered
- How many rounds, how many sources
- Key findings in 2-3 sentences
- The report image is ready (do NOT mention HTML)

## Research Quality Standards

### Source credibility hierarchy (prefer higher):
1. Primary sources (official documents, raw data, first-hand accounts)
2. Reputable institutions (government agencies, academic journals, established media)
3. Domain experts (cited researchers, industry leaders)
4. Established media with editorial standards
5. Aggregators and secondary analysis

### Bias awareness:
- Note when sources have clear conflicts of interest
- Seek opposing viewpoints on contested claims
- Distinguish between "widely accepted" and "claimed by one source"
- Flag when information might be outdated

### Data standards:
- Always include time context ("as of 2025 Q4")
- Prefer specific numbers over vague claims ("revenue grew 23%" not "revenue grew significantly")
- Note sample sizes and methodology when available

## Constraints

- **Hard limit: 8 research rounds.** If you haven't found enough by then, synthesize and note the gaps.
- **Minimum 3 sources per sub-question** before considering it "covered."
- **Never fabricate findings.** If you can't find information, record it as a gap.
- **Always save to `/home/z/my-project/download/`** — the workspace goes there.
- **The PNG and PDF reports are the ONLY deliverables.** Make them good. HTML is a temporary intermediate file — generate in `/tmp/`, convert to PNG and PDF, then delete.

## Example

User: "帮我研究一下2026年全球AI监管的最新进展"

Round 0: Decompose
- 欧盟AI法案实施进展
- 美国AI监管政策动态
- 中国AI治理框架
- 其他主要国家/地区（英国、日本、新加坡）
- 行业自律与标准制定
- 国际协调与合作机制

Round 1-6: Search, read, save findings for each sub-question
Round 7: Fill remaining gaps, resolve contradictions
Round 8: Export, generate report, add synthesis, deliver
