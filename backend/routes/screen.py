import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import httpx

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.database import get_db
from backend.models import Report, Submission

router = APIRouter()

REPORTS_DIR       = os.getenv("REPORTS_DIR", ".tmp/reports")
PROJECT_ROOT      = str(Path(__file__).resolve().parents[2])
MAX_ACCOUNTS      = 10
MAX_SUBMISSIONS_PER_EMAIL = 3
SCRAPE_TIMEOUT    = 420  # 7 min — must be > APIFY_TIMEOUT (300s) + startup overhead
PROFILE_IMGS_DIR  = ".tmp/profile_images"
SCREENSHOTS_DIR   = ".tmp/screenshots"
# Playwright is installed in the Railway Docker image — screenshots enabled by default.
# Set ENABLE_SCREENSHOTS=false to disable if you see Chromium issues.
SCREENSHOTS_ENABLED = os.getenv("ENABLE_SCREENSHOTS", "true").lower() == "true"

# Platform handle → unavatar.io slug
_UNAVATAR_SLUG = {
    "twitter": "twitter", "x": "twitter",
    "instagram": "instagram",
    "tiktok": "tiktok",
    "youtube": "youtube",
    "facebook": "facebook",
}


def _fetch_profile_image_sync(platform: str, handle: str, report_id: str, idx: int) -> str:
    """Download profile avatar via unavatar.io. Returns local file path or ''."""
    slug = _UNAVATAR_SLUG.get(platform.lower(), "")
    if not slug:
        return ""
    clean = handle.lstrip("@").split("?")[0].rstrip("/").split("/")[-1]
    if not clean:
        return ""
    try:
        Path(PROFILE_IMGS_DIR).mkdir(parents=True, exist_ok=True)
        url = f"https://unavatar.io/{slug}/{clean}"
        r = httpx.get(url, timeout=8, follow_redirects=True)
        if r.status_code == 200 and len(r.content) > 500:
            ext = ".jpg"
            out = Path(PROFILE_IMGS_DIR) / f"{report_id}_{idx}{ext}"
            out.write_bytes(r.content)
            return str(out)
    except Exception:
        pass
    return ""


def _capture_screenshots_sync(flagged_posts: list, report_id: str) -> dict:
    """Screenshot each flagged post URL using Playwright. Returns {url: local_path}."""
    posts_with_url = [fp for fp in flagged_posts if (fp.get("post_url") or "").startswith("http")][:5]
    if not posts_with_url:
        return {}
    shots: dict = {}
    try:
        from playwright.sync_api import sync_playwright
        Path(SCREENSHOTS_DIR).mkdir(parents=True, exist_ok=True)
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            ctx = browser.new_context(
                viewport={"width": 640, "height": 900},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
            )
            for i, fp in enumerate(posts_with_url):
                url = fp["post_url"]
                try:
                    page = ctx.new_page()
                    page.goto(url, wait_until="domcontentloaded", timeout=12000)
                    page.wait_for_timeout(2500)
                    out = str(Path(SCREENSHOTS_DIR) / f"{report_id}_{i}.png")
                    page.screenshot(path=out, full_page=False, clip={"x": 0, "y": 0, "width": 640, "height": 700})
                    page.close()
                    shots[url] = out
                except Exception:
                    pass
            browser.close()
    except Exception:
        pass
    return shots


# ── Schemas ───────────────────────────────────────────────────────────────────

class AccountInput(BaseModel):
    platform: str
    handle: str
    manual_posts: Optional[str] = None

    @field_validator("platform")
    @classmethod
    def validate_platform(cls, v):
        allowed = {"twitter", "x", "instagram", "tiktok", "linkedin", "facebook", "youtube"}
        if v.lower() not in allowed:
            raise ValueError(f"Platform must be one of: {', '.join(sorted(allowed))}")
        return v.lower()


class ScreeningRequest(BaseModel):
    name: str
    email: str
    country: str
    accounts: List[AccountInput]
    reason: str
    timeline: str
    consent: bool

    @field_validator("accounts")
    @classmethod
    def validate_accounts(cls, v):
        if not v:
            raise ValueError("At least one social media account is required.")
        if len(v) > MAX_ACCOUNTS:
            raise ValueError(f"Maximum {MAX_ACCOUNTS} accounts allowed per submission.")
        return v

    @field_validator("consent")
    @classmethod
    def must_consent(cls, v):
        if not v:
            raise ValueError("You must authorize screening to proceed.")
        return v


# ── Subprocess scraper ────────────────────────────────────────────────────────

def _run_scraper_sync(platform: str, handle: str) -> list[dict]:
    """Blocking subprocess call — run via executor so the event loop stays free."""
    script = str(Path(PROJECT_ROOT) / "tools" / "scrape_public_profile.py")
    try:
        result = subprocess.run(
            [sys.executable, script, platform, handle],
            capture_output=True,
            cwd=PROJECT_ROOT,
            timeout=SCRAPE_TIMEOUT,
        )
        err_text = result.stderr.decode("utf-8", errors="replace")
        if result.returncode != 0 or not result.stdout.strip():
            return [{"platform": platform,
                     "post_text": f"[SCRAPE_ERROR rc={result.returncode}: {err_text[:400]}]",
                     "post_url": "", "posted_at": None}]
        return json.loads(result.stdout.decode("utf-8", errors="replace"))
    except subprocess.TimeoutExpired:
        return [{"platform": platform, "post_text": "[SCRAPE_ERROR: timeout]",
                 "post_url": "", "posted_at": None}]
    except Exception as e:
        return [{"platform": platform, "post_text": f"[SCRAPE_ERROR: {e}]",
                 "post_url": "", "posted_at": None}]


async def scrape_account_subprocess(platform: str, handle: str) -> list[dict]:
    """Run scraper in a thread pool executor (avoids asyncio subprocess issues on Windows)."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _run_scraper_sync, platform, handle)


# ── Manual post parser ────────────────────────────────────────────────────────

def parse_manual_posts(platform: str, raw: str) -> list[dict]:
    """Split pasted text into individual post dicts for AI analysis."""
    # Split on blank lines first; fall back to single-line splits
    blocks = [b.strip() for b in raw.split("\n\n") if b.strip()]
    if len(blocks) == 1:
        blocks = [b.strip() for b in raw.splitlines() if b.strip()]
    return [
        {"platform": platform, "post_text": block, "post_url": "", "posted_at": None}
        for block in blocks[:50]  # cap at 50
    ]


# ── Background job ────────────────────────────────────────────────────────────

async def run_screening_job(report_id: str, submission_data: dict):
    from backend.database import AsyncSessionLocal
    from tools.analyze_with_ai import analyze_posts
    from tools.generate_pdf import generate_pdf

    async with AsyncSessionLocal() as db:
        report = await db.get(Report, report_id)
        if not report:
            return

        report.status = "processing"
        report.updated_at = datetime.utcnow()
        await db.commit()

        try:
            accounts = submission_data.get("accounts", [])

            # 1. Collect posts — use pasted text when provided, else scrape
            all_posts: list[dict] = []
            for acc in accounts:
                platform = acc.get("platform", "twitter")
                manual = acc.get("manual_posts", "")
                if manual and manual.strip():
                    posts = parse_manual_posts(platform, manual.strip())
                else:
                    posts = await scrape_account_subprocess(platform, acc.get("handle", ""))
                all_posts.extend(posts)

            # 2. AI analysis (blocking — run in thread pool)
            loop = asyncio.get_event_loop()
            analysis = await loop.run_in_executor(
                None,
                analyze_posts,
                all_posts,
                submission_data["name"],
                submission_data["country"],
                submission_data["reason"],
            )

            # Enrich with submission metadata for PDF
            analysis["name"]     = submission_data["name"]
            analysis["country"]  = submission_data["country"]
            analysis["reason"]   = submission_data["reason"]
            analysis["accounts"] = accounts

            # 3a. Fetch profile images for each account (non-blocking failures ignored)
            enriched_accounts = []
            for idx, acc in enumerate(accounts):
                img_path = await loop.run_in_executor(
                    None, _fetch_profile_image_sync,
                    acc.get("platform", ""), acc.get("handle", ""), report_id, idx,
                )
                enriched_accounts.append({**acc, "profile_image": img_path})
            analysis["accounts"] = enriched_accounts

            # 3b. Screenshots — only if explicitly enabled (Playwright hangs on Railway)
            flagged = analysis.get("flagged_posts", [])
            if flagged and SCREENSHOTS_ENABLED:
                try:
                    screenshots = await asyncio.wait_for(
                        loop.run_in_executor(None, _capture_screenshots_sync, flagged, report_id),
                        timeout=25.0,
                    )
                except Exception:
                    screenshots = {}
                for fp in flagged:
                    url = fp.get("post_url", "")
                    if url and url in screenshots:
                        fp["screenshot_path"] = screenshots[url]

            # 4. Generate PDF (blocking — run in thread pool)
            Path(REPORTS_DIR).mkdir(parents=True, exist_ok=True)
            pdf_path = f"{REPORTS_DIR}/{report_id}.pdf"
            await loop.run_in_executor(None, generate_pdf, analysis, pdf_path)

            report.status      = "done"
            report.report_json = analysis
            report.pdf_path    = pdf_path

        except Exception as exc:
            import traceback
            tb = traceback.format_exc()
            print(f"[SCREENING ERROR] job={report_id}\n{tb}", flush=True)
            report.status        = "failed"
            report.error_message = tb[:3000]

        report.updated_at = datetime.utcnow()
        await db.commit()


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/screen")
async def submit_screening(
    req: ScreeningRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    # Rate limit: 3 per email
    count_result = await db.execute(
        select(func.count()).where(Submission.email == req.email)
    )
    if (count_result.scalar() or 0) >= MAX_SUBMISSIONS_PER_EMAIL:
        raise HTTPException(
            status_code=429,
            detail=f"Maximum {MAX_SUBMISSIONS_PER_EMAIL} submissions per email address.",
        )

    submission = Submission(
        name     = req.name,
        email    = req.email,
        country  = req.country,
        accounts = [a.model_dump() for a in req.accounts],
        reason   = req.reason,
        timeline = req.timeline,
    )
    db.add(submission)
    await db.flush()

    report = Report(submission_id=submission.id, status="queued")
    db.add(report)
    await db.commit()
    await db.refresh(report)

    # Pass plain dict — avoids SQLAlchemy session issues in background task
    submission_data = {
        "name":     req.name,
        "email":    req.email,
        "country":  req.country,
        "reason":   req.reason,
        "timeline": req.timeline,
        "accounts": [a.model_dump() for a in req.accounts],
    }

    background_tasks.add_task(run_screening_job, report.id, submission_data)

    return {"job_id": report.id, "status": "queued"}


@router.get("/status/{job_id}")
async def get_status(job_id: str, db: AsyncSession = Depends(get_db)):
    report = await db.get(Report, job_id)
    if not report:
        raise HTTPException(status_code=404, detail="Job not found.")
    return {
        "job_id": job_id,
        "status": report.status,
        "error":  report.error_message,
    }
