# Workflow: Generate Screening Report

## Objective
Transform raw scraped posts + applicant metadata into a structured risk report and branded PDF.

## Inputs Required
- `posts` (list): [{platform, post_text, post_url, posted_at}]
- `name`, `country`, `reason` (str): Applicant metadata

## Steps

### 1. Filter Posts
- Remove entries where `post_text` starts with `[SCRAPE_ERROR`
- Cap at 50 posts per account
- Deduplicate by text content

### 2. Build AI Prompt
Template: `tools/analyze_with_ai.py → ANALYSIS_PROMPT_TEMPLATE`
- Include post count, platform count, applicant info
- System role: immigration compliance analyst
- Response format: `json_object`
- Model: `gpt-4o`, temperature: 0.2, max_tokens: 4000

### 3. Parse AI Output
Expected fields:
- `overall_risk`: HIGH | MEDIUM | LOW
- `risk_score`: 0–100
- `scores`: {political, content, network}
- `summary`: 2–3 paragraph string
- `flagged_posts`: list (max 10)
- `risk_topics`: list of strings
- `sentiment`: {positive, neutral, negative} — must sum to 100
- `recommendations`: list of strings
- `overall_assessment`: one sentence

### 4. Generate PDF (ReportLab)
Pages:
1. **Cover** (manual canvas): gradient background, subject name, risk badge, 3 gauges, metadata table
2. **AI Summary**: header + body text + risk topics
3. **Security Threat Table**: category | count | risk level | concern
4. **Flagged Posts**: expandable cards with post text + explanation
5. **Recommendations**: numbered list
6. **Overall Assessment** + disclaimer

### 5. Merge PDFs
Use `pypdf.PdfWriter` to merge cover + body into single file.

## Risk Score Interpretation
| Score | Level  | Color  |
|-------|--------|--------|
| 0–30  | LOW    | Green  |
| 31–60 | MEDIUM | Orange |
| 61–100| HIGH   | Red    |

## Notes
- If `pypdf` is not installed, the body-only PDF is used as the final output.
- Watermark "CONFIDENTIAL" is on cover page only.
- Gauge arcs use ReportLab `canvas.arc` — angles are in degrees, 0° = right, 90° = top.
