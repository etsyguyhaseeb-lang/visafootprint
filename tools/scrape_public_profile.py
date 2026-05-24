"""
Self-hosted scrapers — zero dependency on ScrapeCreators or Apify.

Priority per platform (all free, all self-hosted):
  Twitter/X  — Twitter API v2 free tier → Playwright + cookies
  Instagram  — instaloader (public) → Instagram internal API + cookies
  TikTok     — yt-dlp (no auth needed)
  YouTube    — yt-dlp → YouTube Data API v3 (free quota)
  Facebook   — Playwright headless (public) → Playwright + cookies
  LinkedIn   — Apify curious_coder~linkedin-posts-scraper (paid) → manual paste fallback

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
        print(f"[APIFY] No token — skipping {actor_id}", file=sys.stderr, flush=True)
        return []
    try:
        print(f"[APIFY] Running {actor_id} ...", file=sys.stderr, flush=True)
        r = httpx.post(
            f"https://api.apify.com/v2/acts/{actor_id}/run-sync-get-dataset-items",
            params={"token": APIFY_TOKEN, "limit": MAX_POSTS},
            json=input_data, timeout=APIFY_TIMEOUT)
        print(f"[APIFY] {actor_id} → HTTP {r.status_code}", file=sys.stderr, flush=True)
        if r.status_code not in (200, 201):
            print(f"[APIFY] Error body: {r.text[:400]}", file=sys.stderr, flush=True)
            return []
        data = r.json()
        result = data if isinstance(data, list) else []
        print(f"[APIFY] {actor_id} → {len(result)} items", file=sys.stderr, flush=True)
        return result
    except Exception as e:
        print(f"[APIFY] {actor_id} exception: {e}", file=sys.stderr, flush=True)
        return []


# ── Twitter / X ────────────────────────────────────────────────────────────────

def scrape_twitter(handle: str) -> list[dict]:
    profile_url = f"https://x.com/{handle}"

    # 1. Official Twitter API v2 — free, reliable, always try first
    if TWITTER_BEARER_TOKEN:
        posts = scrape_twitter_apiv2(handle)
        if _is_ok(posts):
            return posts

    # 2. ScrapeCreators paid API
    if _USE_PAID and SCRAPECREATORS_KEY:
        items = _sc_paginate("/v1/twitter/user-tweets", {"handle": handle},
                             items_key="tweets", next_key="nextCursor")
        if items:
            results = [{"platform": "Twitter/X",
                        "post_text": (i.get("text") or i.get("full_text") or "").strip(),
                        "post_url":  i.get("url") or f"https://x.com/{handle}/status/{i.get('id','')}",
                        "posted_at": i.get("createdAt") or i.get("created_at")}
                       for i in items if isinstance(i, dict) and (i.get("text") or i.get("full_text") or "").strip()]
            if results:
                return results

    # 3. Apify Twitter scraper
    if _USE_PAID and APIFY_TOKEN:
        apify = _apify_run("vdrmota~twitter-scraper",
                           {"startUrls": [{"url": f"https://twitter.com/{handle}"}],
                            "maxItems": MAX_POSTS})
        if apify:
            results = [{"platform": "Twitter/X",
                        "post_text": i.get("full_text") or i.get("text") or "",
                        "post_url":  f"https://x.com/{handle}/status/{i.get('id_str','')}",
                        "posted_at": i.get("created_at")}
                       for i in apify if isinstance(i, dict) and (i.get("full_text") or i.get("text")) and not i.get("noResults")]
            if results:
                return results

    # 4. Playwright-based own scraper (needs cookies on server)
    posts = scrape_twitter_own(handle)
    if _is_ok(posts):
        return posts

    return _err("Twitter/X",
                "Profile may be protected or has no public tweets",
                profile_url)


# ── Instagram ──────────────────────────────────────────────────────────────────

def scrape_instagram(handle: str) -> list[dict]:
    profile_url = f"https://www.instagram.com/{handle}/"

    # Production: Apify runs FIRST
    if _USE_PAID:
        items = _sc_paginate("/v2/instagram/user/posts", {"handle": handle},
                             items_key="data", next_key="nextCursor")
        if items:
            results = [{"platform": "Instagram",
                        "post_text": (p.get("caption") or p.get("text") or "").strip(),
                        "post_url":  p.get("url") or (f"https://www.instagram.com/p/{p['shortCode']}/"
                                                       if p.get("shortCode") else profile_url),
                        "posted_at": p.get("timestamp") or p.get("takenAt")}
                       for p in items if isinstance(p, dict) and (p.get("caption") or p.get("text") or "").strip()]
            if results:
                return results

        apify = _apify_run("apify~instagram-post-scraper",
                           {"username": [handle], "resultsLimit": MAX_POSTS})
        if apify:
            results = [{"platform": "Instagram",
                        "post_text": (p.get("caption") or "").strip(),
                        "post_url":  p.get("url") or profile_url,
                        "posted_at": p.get("timestamp")}
                       for p in apify[:MAX_POSTS] if isinstance(p, dict) and (p.get("caption") or "").strip()]
            if results:
                return results

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
            results = [{"platform": "TikTok",
                        "post_text": (i.get("text") or i.get("description") or i.get("desc") or "").strip()
                                     or "[Video — no caption]",
                        "post_url":  i.get("url") or profile_url,
                        "posted_at": i.get("createTime") or i.get("createTimeISO")}
                       for i in items if isinstance(i, dict) and i.get("id")]
            if results:
                return results

        apify = _apify_run("clockworks~tiktok-profile-scraper",
                           {"profiles": [f"https://www.tiktok.com/@{handle}"],
                            "shouldDownloadCovers": False,
                            "shouldDownloadVideos": False,
                            "maxPostsPerProfile": MAX_POSTS})
        if apify:
            results = [{"platform": "TikTok",
                        "post_text": (i.get("text") or i.get("desc") or "").strip() or "[Video — no caption]",
                        "post_url":  i.get("webVideoUrl") or profile_url,
                        "posted_at": (str(datetime.fromtimestamp(i["createTime"]))
                                      if i.get("createTime") else i.get("createTimeISO"))}
                       for i in apify if isinstance(i, dict) and i.get("id") and not i.get("noResults")]
            if results:
                return results

    # Local dev: yt-dlp fallback
    posts = scrape_tiktok_own(handle)
    if _is_ok(posts):
        return posts

    return _err("TikTok",
                "TikTok blocked access — run save-cookies to authenticate yt-dlp",
                profile_url)


# ── Facebook ───────────────────────────────────────────────────────────────────

def _parse_fb_item(item: dict, fb_url: str) -> dict | None:
    """Normalise a Facebook Apify result — handles field name variants across actors."""
    if not isinstance(item, dict):
        return None
    text = (
        item.get("text") or item.get("message") or item.get("story") or
        item.get("postText") or item.get("content") or ""
    ).strip()
    if not text:
        return None
    url = (
        item.get("url") or item.get("postUrl") or item.get("link") or
        item.get("permalinkUrl") or fb_url
    )
    ts = (
        item.get("time") or item.get("timestamp") or item.get("date") or
        item.get("createdTime") or item.get("created_time")
    )
    return {"platform": "Facebook", "post_text": text, "post_url": url, "posted_at": str(ts or "")}


def scrape_facebook(handle: str) -> list[dict]:
    fb_url = handle if handle.startswith("http") else f"https://www.facebook.com/{handle}"

    if _USE_PAID:
        # ScrapeCreators first (cheapest)
        items = _sc_paginate("/v1/facebook/profile/posts", {"url": fb_url},
                             items_key="posts", next_key="nextCursor")
        if items:
            results = [r for r in (_parse_fb_item(p, fb_url) for p in items) if r]
            if results:
                return results[:MAX_POSTS]

        # Apify: try apify~facebook-pages-scraper (current reliable actor)
        apify = _apify_run("apify~facebook-pages-scraper",
                           {"startUrls": [{"url": fb_url}],
                            "maxPosts": MAX_POSTS,
                            "maxComments": 0,
                            "scrapeAbout": False,
                            "scrapeReviews": False,
                            "scrapeEvents": False})
        if apify:
            results = [r for r in (_parse_fb_item(i, fb_url) for i in apify) if r]
            if results:
                return results[:MAX_POSTS]

        # Apify fallback: apify~facebook-posts-scraper (legacy actor)
        apify2 = _apify_run("apify~facebook-posts-scraper",
                            {"startUrls": [{"url": fb_url}],
                             "maxPosts": MAX_POSTS, "maxPostsPerPage": MAX_POSTS,
                             "maxComments": 0, "scrapeAbout": False, "scrapeReviews": False})
        if apify2:
            results = [r for r in (_parse_fb_item(i, fb_url) for i in apify2) if r]
            if results:
                return results[:MAX_POSTS]

    # Self-hosted Playwright fallback (works without cookies for public pages)
    posts = scrape_facebook_own(handle)
    if _is_ok(posts):
        return posts

    return _err("Facebook",
                "Facebook requires login cookies or paid Apify — run save-cookies to authenticate",
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

def _parse_li_item(item: dict, profile_url: str) -> dict | None:
    """Normalise a LinkedIn Apify result — handles field name variants across actors."""
    if not isinstance(item, dict):
        return None
    text = (
        item.get("text") or item.get("commentary") or item.get("content") or
        item.get("postText") or item.get("description") or
        # some actors nest it under 'article'
        (item.get("article") or {}).get("title") or ""
    ).strip()
    if not text:
        return None
    url = (
        item.get("url") or item.get("postUrl") or item.get("link") or
        item.get("shareUrl") or profile_url
    )
    ts = (
        item.get("postedAt") or item.get("publishedAt") or item.get("date") or
        item.get("createdAt") or item.get("timestamp")
    )
    return {"platform": "LinkedIn", "post_text": text, "post_url": url, "posted_at": str(ts or "")}


def scrape_linkedin(handle: str) -> list[dict]:
    # Accept full LinkedIn URLs too
    if handle.startswith("http"):
        profile_url = handle if handle.endswith("/") else handle + "/"
    else:
        profile_url = f"https://www.linkedin.com/in/{handle}/"

    if not _USE_PAID:
        return _err("LinkedIn",
                    "LinkedIn requires Apify (set USE_PAID_SCRAPERS=true) or use the 'Paste posts' option",
                    profile_url)

    # Actor 1: curious_coder~linkedin-posts-scraper (most popular)
    apify = _apify_run("curious_coder~linkedin-posts-scraper",
                       {"profileUrls": [profile_url], "maxPosts": MAX_POSTS})
    if apify:
        results = [r for r in (_parse_li_item(i, profile_url) for i in apify) if r]
        if results:
            return results[:MAX_POSTS]

    # Actor 2: dev_fusion~linkedin-profile-posts-scraper (alternative)
    apify2 = _apify_run("dev_fusion~linkedin-profile-posts-scraper",
                        {"profileUrl": profile_url, "maxPosts": MAX_POSTS})
    if apify2:
        results = [r for r in (_parse_li_item(i, profile_url) for i in apify2) if r]
        if results:
            return results[:MAX_POSTS]

    # Actor 3: bebity~linkedin-profile-scraper (another fallback)
    apify3 = _apify_run("bebity~linkedin-profile-scraper",
                        {"profileUrls": [profile_url], "maxResults": MAX_POSTS})
    if apify3:
        results = [r for r in (_parse_li_item(i, profile_url) for i in apify3) if r]
        if results:
            return results[:MAX_POSTS]

    return _err("LinkedIn",
                "LinkedIn scraping failed via Apify — use the 'Paste posts' option as fallback",
                profile_url)


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
