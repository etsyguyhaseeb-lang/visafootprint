"""
Self-hosted scrapers — zero dependency on ScrapeCreators or Apify.

Priority per platform (all free, all self-hosted):
  Twitter/X  — Twitter API v2 free tier → Playwright + cookies
  Instagram  — instaloader (public) → Instagram internal API + cookies
  TikTok     — yt-dlp (no auth needed)
  YouTube    — yt-dlp → YouTube Data API v3 (free quota)
  Facebook   — Playwright headless (public) → Playwright + cookies
  LinkedIn   — manual paste only (LinkedIn blocks all bots)

Optional paid fallback (only activates if USE_PAID_SCRAPERS=true in .env):
  ScrapeCreators / Apify — used ONLY as last resort if all own scrapers fail
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import httpx
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scraper_own import (
    scrape_instagram_own,
    scrape_facebook_own,
    scrape_tiktok_own,
    scrape_twitter_own,
    scrape_twitter_apiv2,
    scrape_twitter_public,
    scrape_youtube_own,
)

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# Own free API keys
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN", "")
YOUTUBE_API_KEY      = os.getenv("YOUTUBE_API_KEY", "")

# Paid fallbacks — opt-in only (set USE_PAID_SCRAPERS=true in .env to enable)
_USE_PAID          = os.getenv("USE_PAID_SCRAPERS", "false").lower() == "true"
SCRAPECREATORS_KEY = os.getenv("SCRAPECREATORS_API_KEY", "") if _USE_PAID else ""
APIFY_TOKEN        = os.getenv("APIFY_API_TOKEN", "")        if _USE_PAID else ""

MAX_POSTS     = 50
SC_BASE_URL   = "https://api.scrapecreators.com"
APIFY_TIMEOUT = 300


# ── Helpers ────────────────────────────────────────────────────────────────────

def normalize_handle(platform: str, raw: str) -> str:
    raw = raw.strip().lstrip("@")
    if not raw.startswith("http"):
        return raw
    parsed = urlparse(raw)
    # Preserve full URL when query string carries identity (e.g. profile.php?id=...)
    if parsed.query:
        return raw
    path   = parsed.path.strip("/")
    parts  = [p for p in path.split("/") if p]
    skip   = {"in", "user", "channel"}
    for part in parts:
        clean = part.lstrip("@")
        if clean and clean not in skip:
            return clean
    return parts[-1].lstrip("@") if parts else raw


def _err(platform: str, msg: str, url: str = "") -> list[dict]:
    return [{"platform": platform, "post_text": f"[SCRAPE_ERROR: {msg}]",
             "post_url": url, "posted_at": None}]


def _is_ok(posts: list[dict]) -> bool:
    return bool(posts) and not posts[0]["post_text"].startswith("[SCRAPE_ERROR")


# ── Optional paid fallback helpers ────────────────────────────────────────────

def _sc_paginate(endpoint: str, base_params: dict,
                 items_key: str, cursor_key: str = "cursor",
                 next_key: str = "nextCursor") -> list[dict]:
    if not SCRAPECREATORS_KEY:
        return []
    all_items: list = []
    params = dict(base_params)
    while len(all_items) < MAX_POSTS:
        try:
            r = httpx.get(f"{SC_BASE_URL}{endpoint}",
                          headers={"x-api-key": SCRAPECREATORS_KEY},
                          params=params, timeout=30)
            if r.status_code != 200:
                break
            data  = r.json()
            page  = data.get(items_key) if isinstance(data, dict) else data
            if not isinstance(page, list) or not page:
                break
            all_items.extend(page)
            cursor = (data.get(next_key) or data.get("cursor") or "") if isinstance(data, dict) else ""
            if not cursor or len(all_items) >= MAX_POSTS:
                break
            params[cursor_key] = cursor
        except Exception:
            break
    return all_items[:MAX_POSTS]


def _apify_run(actor_id: str, input_data: dict) -> list[dict]:
    if not APIFY_TOKEN:
        return []
    try:
        r = httpx.post(
            f"https://api.apify.com/v2/acts/{actor_id}/run-sync-get-dataset-items",
            params={"token": APIFY_TOKEN}, json=input_data, timeout=APIFY_TIMEOUT)
        return r.json() if r.status_code in (200, 201) else []
    except Exception:
        return []


# ── Twitter / X ────────────────────────────────────────────────────────────────

def scrape_twitter(handle: str) -> list[dict]:
    profile_url = f"https://x.com/{handle}"

    # Production: Apify runs FIRST — own scrapers need cookies that don't exist on the server
    if _USE_PAID:
        items = _sc_paginate("/v1/twitter/user-tweets", {"handle": handle},
                             items_key="tweets", next_key="nextCursor")
        if items:
            return [{"platform": "Twitter/X",
                     "post_text": (i.get("text") or i.get("full_text") or "").strip(),
                     "post_url":  i.get("url") or f"https://x.com/{handle}/status/{i.get('id','')}",
                     "posted_at": i.get("createdAt") or i.get("created_at")}
                    for i in items if (i.get("text") or i.get("full_text") or "").strip()]

        apify = _apify_run("vdrmota~twitter-scraper",
                           {"startUrls": [{"url": f"https://twitter.com/{handle}"}],
                            "maxItems": MAX_POSTS})
        if apify:
            return [{"platform": "Twitter/X",
                     "post_text": i.get("full_text") or i.get("text") or "",
                     "post_url":  f"https://x.com/{handle}/status/{i.get('id_str','')}",
                     "posted_at": i.get("created_at")}
                    for i in apify if (i.get("full_text") or i.get("text")) and not i.get("noResults")]

    # Local dev: own scrapers first
    posts = scrape_twitter_own(handle)
    if _is_ok(posts):
        return posts

    posts = scrape_twitter_public(handle)
    if _is_ok(posts):
        return posts

    if TWITTER_BEARER_TOKEN:
        posts = scrape_twitter_apiv2(handle)
        if _is_ok(posts):
            return posts

    return _err("Twitter/X",
                "Profile may be protected — try saving Twitter cookies via save-cookies",
                profile_url)


# ── Instagram ──────────────────────────────────────────────────────────────────

def scrape_instagram(handle: str) -> list[dict]:
    profile_url = f"https://www.instagram.com/{handle}/"

    # Production: Apify runs FIRST
    if _USE_PAID:
        items = _sc_paginate("/v2/instagram/user/posts", {"handle": handle},
                             items_key="data", next_key="nextCursor")
        if items:
            return [{"platform": "Instagram",
                     "post_text": (p.get("caption") or p.get("text") or "").strip(),
                     "post_url":  p.get("url") or (f"https://www.instagram.com/p/{p['shortCode']}/"
                                                    if p.get("shortCode") else profile_url),
                     "posted_at": p.get("timestamp") or p.get("takenAt")}
                    for p in items if (p.get("caption") or p.get("text") or "").strip()]

        apify = _apify_run("apify~instagram-post-scraper",
                           {"username": [handle], "resultsLimit": MAX_POSTS})
        if apify:
            return [{"platform": "Instagram",
                     "post_text": (p.get("caption") or "").strip(),
                     "post_url":  p.get("url") or profile_url,
                     "posted_at": p.get("timestamp")}
                    for p in apify[:MAX_POSTS] if (p.get("caption") or "").strip()]

    # Local dev: instaloader fallback
    posts = scrape_instagram_own(handle)
    if _is_ok(posts):
        return posts

    return _err("Instagram",
                "Profile may be private, or run save-cookies for authenticated scraping",
                profile_url)


# ── TikTok ─────────────────────────────────────────────────────────────────────

def scrape_tiktok(handle: str) -> list[dict]:
    profile_url = f"https://www.tiktok.com/@{handle}"

    # Production: Apify runs FIRST
    if _USE_PAID:
        items = _sc_paginate("/v3/tiktok/profile/videos", {"handle": handle},
                             items_key="videos", next_key="nextCursor")
        if items:
            return [{"platform": "TikTok",
                     "post_text": (i.get("text") or i.get("description") or i.get("desc") or "").strip()
                                  or "[Video — no caption]",
                     "post_url":  i.get("url") or profile_url,
                     "posted_at": i.get("createTime") or i.get("createTimeISO")}
                    for i in items if i.get("id")]

        apify = _apify_run("clockworks~tiktok-profile-scraper",
                           {"profiles": [f"https://www.tiktok.com/@{handle}"],
                            "shouldDownloadCovers": False,
                            "shouldDownloadVideos": False,
                            "maxPostsPerProfile": MAX_POSTS})
        if apify:
            return [{"platform": "TikTok",
                     "post_text": (i.get("text") or i.get("desc") or "").strip() or "[Video — no caption]",
                     "post_url":  i.get("webVideoUrl") or profile_url,
                     "posted_at": (str(datetime.fromtimestamp(i["createTime"]))
                                   if i.get("createTime") else i.get("createTimeISO"))}
                    for i in apify if i.get("id") and not i.get("noResults")]

    # Local dev: yt-dlp fallback
    posts = scrape_tiktok_own(handle)
    if _is_ok(posts):
        return posts

    return _err("TikTok",
                "TikTok blocked access — run save-cookies to authenticate yt-dlp",
                profile_url)


# ── Facebook ───────────────────────────────────────────────────────────────────

def scrape_facebook(handle: str) -> list[dict]:
    fb_url = handle if handle.startswith("http") else f"https://www.facebook.com/{handle}"

    # Production: Apify runs FIRST
    if _USE_PAID:
        items = _sc_paginate("/v1/facebook/profile/posts", {"url": fb_url},
                             items_key="posts", next_key="nextCursor")
        if items:
            return [{"platform": "Facebook",
                     "post_text": (p.get("text") or p.get("message") or "").strip(),
                     "post_url":  p.get("url") or fb_url,
                     "posted_at": p.get("time") or p.get("timestamp")}
                    for p in items if (p.get("text") or p.get("message") or "").strip()]

        apify = _apify_run("apify~facebook-posts-scraper",
                           {"startUrls": [{"url": fb_url}],
                            "maxPosts": MAX_POSTS, "maxPostsPerPage": MAX_POSTS,
                            "maxComments": 0, "scrapeAbout": False, "scrapeReviews": False})
        if apify:
            return [{"platform": "Facebook",
                     "post_text": (i.get("text") or i.get("message") or "").strip(),
                     "post_url":  i.get("url") or fb_url,
                     "posted_at": i.get("time") or i.get("timestamp")}
                    for i in apify if (i.get("text") or i.get("message") or "").strip()]

    # Local dev: Playwright fallback
    posts = scrape_facebook_own(handle)
    if _is_ok(posts):
        return posts

    return _err("Facebook",
                "Facebook shows limited content without login — run save-cookies to authenticate",
                fb_url)


# ── YouTube ────────────────────────────────────────────────────────────────────

def scrape_youtube(handle: str) -> list[dict]:
    if handle.startswith("http"):
        channel_url = handle
    elif handle.startswith("@"):
        channel_url = f"https://www.youtube.com/{handle}"
    else:
        channel_url = f"https://www.youtube.com/@{handle}"

    # Production: YouTube Data API first, then yt-dlp as fallback
    # (yt-dlp also works on Railway since it doesn't need cookies)
    posts = scrape_youtube_own(handle)
    if _is_ok(posts):
        return posts

    if YOUTUBE_API_KEY:
        try:
            with httpx.Client(timeout=30) as client:
                r = client.get(
                    "https://www.googleapis.com/youtube/v3/search",
                    params={"part": "snippet", "q": handle, "type": "channel",
                            "key": YOUTUBE_API_KEY, "maxResults": 1})
                items = r.json().get("items", [])
                if not items:
                    return _err("YouTube", "Channel not found", channel_url)
                channel_id = items[0]["snippet"]["channelId"]
                r2 = client.get(
                    "https://www.googleapis.com/youtube/v3/search",
                    params={"part": "snippet", "channelId": channel_id,
                            "type": "video", "order": "date",
                            "maxResults": 50, "key": YOUTUBE_API_KEY})
                vids = [
                    {"platform": "YouTube",
                     "post_text": (f"{v['snippet']['title']}. "
                                   f"{v['snippet'].get('description', '')}").strip(". "),
                     "post_url":  f"https://www.youtube.com/watch?v={v['id']['videoId']}",
                     "posted_at": v["snippet"]["publishedAt"]}
                    for v in r2.json().get("items", [])
                    if v["snippet"].get("title")
                ]
                return vids if vids else _err("YouTube", "No videos found", channel_url)
        except Exception as e:
            return _err("YouTube", str(e)[:200], channel_url)

    return _err("YouTube",
                "yt-dlp failed — run: pip install -U yt-dlp",
                channel_url)


# ── LinkedIn ───────────────────────────────────────────────────────────────────

def scrape_linkedin(handle: str) -> list[dict]:
    return _err("LinkedIn",
                "LinkedIn blocks all automated scraping — use the 'Paste posts' option in the form",
                f"https://www.linkedin.com/in/{handle}/")


# ── Router ─────────────────────────────────────────────────────────────────────

SCRAPERS = {
    "twitter":   scrape_twitter,
    "x":         scrape_twitter,
    "instagram": scrape_instagram,
    "tiktok":    scrape_tiktok,
    "linkedin":  scrape_linkedin,
    "facebook":  scrape_facebook,
    "youtube":   scrape_youtube,
}


def scrape_profile(platform: str, handle_or_url: str) -> list[dict]:
    handle = normalize_handle(platform, handle_or_url)
    fn     = SCRAPERS.get(platform.lower(), scrape_twitter)
    return fn(handle)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.stdout.buffer.write(
            b"Usage: python scrape_public_profile.py <platform> <handle_or_url>\n")
        sys.exit(1)
    results = scrape_profile(sys.argv[1], sys.argv[2])
    sys.stdout.buffer.write(json.dumps(results, ensure_ascii=False).encode("utf-8"))
    sys.stdout.buffer.write(b"\n")
