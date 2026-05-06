# Workflow: Screen Social Media Profile

## Objective
Accept a user's screening form submission, scrape their social media profiles, run AI risk analysis, generate a PDF report, and persist results.

## Inputs Required
- `name` (str): Applicant full name
- `email` (str): Contact email
- `country` (str): Country of origin
- `accounts` (list): [{platform, handle}] — up to 10
- `reason` (str): Reason for screening
- `timeline` (str): Visa application timeline
- `consent` (bool): Must be true

## Steps

1. **Validate input** → `backend/routes/screen.py`
   - Check email submission count ≤ 3 (rate limit)
   - Validate accounts ≤ 10
   - Ensure consent = true

2. **Create DB records** → `backend/models.py`
   - Insert `Submission` row
   - Insert `Report` row with status = `queued`

3. **Scrape profiles** → `tools/scrape_public_profile.py`
   - For each account: call `scrape_profile(platform, handle)`
   - Uses Playwright headless Chromium
   - Cap at 50 posts per account
   - On scrape failure: append error post, continue (partial analysis)
   - Retry logic: exponential backoff on timeout

4. **AI Analysis** → `tools/analyze_with_ai.py`
   - Feed all posts + metadata to `gpt-4o`
   - Get structured JSON with risk scores, flagged posts, recommendations
   - If zero real posts: return low-risk result with note

5. **Generate PDF** → `tools/generate_pdf.py`
   - Build cover page (canvas)
   - Build body pages (Platypus)
   - Merge via pypdf → `.tmp/reports/{report_id}.pdf`

6. **Update DB** → `backend/routes/screen.py`
   - Set `Report.status = "done"`
   - Store `report_json`, `pdf_path`

## Expected Output
- `Report.status = "done"`
- `Report.report_json` = full analysis dict
- `Report.pdf_path` = `.tmp/reports/{id}.pdf`

## Edge Cases & Notes
- **Twitter blocking**: Playwright may get rate-limited or blocked. Fallback: return partial analysis.
- **Private profiles**: Scraper returns empty posts. Report states "private profile — unable to analyze."
- **OpenAI timeout**: Retry once with a shorter prompt if first call exceeds 60s.
- **pypdf not installed**: PDF merge skips to body-only; install `pypdf` via pip.
- **Rate limiting email**: After 3 submissions the API returns 429.
