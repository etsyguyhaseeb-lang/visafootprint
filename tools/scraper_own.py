"""
Free self-hosted scrapers — zero API cost.

Strategy per platform:
  Twitter   — Official API v2 free tier (add TWITTER_BEARER_TOKEN to .env)
  TikTok    — yt-dlp (best open-source tool, no login needed for public profiles)
  Facebook  — Playwright + saved browser cookies (log in once, scrapes forever)
  Instagram — instaloader first, then Playwright + saved cookies

Cookie setup (one-time, opens real browser window):
  python tools/scraper_own.py save-cookies
"""

import httpx
import json
import sys
import time
from pathlib import Path

MAX_POSTS    = 500
COOKIES_FILE = Path(__file__).resolve().parents[1] / ".tmp" / "cookies.json"

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def _err(platform: str, msg: str, url: str = "") -> list[dict]:
    return [{"platform": platform, "post_text": f"[SCRAPE_ERROR: {msg}]",
             "post_url": url, "posted_at": None}]


def _load_cookies(domain: str) -> list[dict]:
    if not COOKIES_FILE.exists():
        return []
    try:
        raw = json.loads(COOKIES_FILE.read_text())
    except Exception:
        return []
    result = []
    for c in raw:
        if domain not in c.get("domain", ""):
            continue
        # Playwright only accepts Strict | Lax | None
        same_site = (c.get("sameSite") or "Lax")
        if same_site.lower() in ("no_restriction", "unspecified", "none"):
            same_site = "None"
        elif same_site.lower() == "strict":
            same_site = "Strict"
        else:
            same_site = "Lax"
        result.append({**c, "sameSite": same_site})
    return result


def _netscape_cookies_file() -> str:
    """Write a Netscape-format cookies file for yt-dlp and return its path."""
    if not COOKIES_FILE.exists():
        return ""
    try:
        cookies = json.loads(COOKIES_FILE.read_text())
    except Exception:
        return ""
    netscape_path = str(COOKIES_FILE).replace(".json", ".txt")
    lines = ["# Netscape HTTP Cookie File"]
    for c in cookies:
        domain  = c.get("domain", "")
        flag    = "TRUE" if domain.startswith(".") else "FALSE"
        path    = c.get("path", "/")
        secure  = "TRUE" if c.get("secure") else "FALSE"
        exp     = str(int(c.get("expirationDate", 0) or 0))
        name    = c.get("name", "")
        value   = c.get("value", "")
        lines.append(f"{domain}\t{flag}\t{path}\t{secure}\t{exp}\t{name}\t{value}")
    Path(netscape_path).write_text("\n".join(lines), encoding="utf-8")
    return netscape_path


def _has_cookies(domain: str) -> bool:
    return bool(_load_cookies(domain))


# ── TikTok via yt-dlp ─────────────────────────────────────────────────────────

def scrape_tiktok_own(handle: str) -> list[dict]:
    """Try yt-dlp first; fall back to Playwright if secUID extraction fails."""
    profile_url = f"https://www.tiktok.com/@{handle}"
    try:
        import yt_dlp
    except ImportError:
        return _scrape_tiktok_playwright(handle, profile_url)

    netscape = _netscape_cookies_file()
    # extract_flat=True fetches the video list quickly without per-video API calls.
    # Full detail mode (no extract_flat) gets captions but can take 60-120s per profile.
    has_cookies = bool(netscape)
    ydl_opts = {
        "quiet":          True,
        "no_warnings":    True,
        "skip_download":  True,
        "extract_flat":   not has_cookies,
        "playlistend":    20,
        "ignoreerrors":   True,
        "socket_timeout": 15,
        "retries":        1,
        "fragment_retries": 1,
        "http_headers":   {"User-Agent": UA},
    }
    if netscape:
        ydl_opts["cookiefile"] = netscape

    # curl-cffi impersonation helps when doing full detail fetches (with cookies).
    # Don't use it for flat listing — it overrides extract_flat and makes things slow.
    if has_cookies:
        try:
            from yt_dlp.networking._curlcffi import CurlCFFIRH  # noqa: F401
            from yt_dlp.networking.impersonate import ImpersonateTarget
            ydl_opts["impersonate"] = ImpersonateTarget("chrome")
        except Exception:
            pass

    try:
        posts = []
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(profile_url, download=False)
            if not info:
                return _scrape_tiktok_playwright(handle, profile_url)
            entries = info.get("entries") or ([info] if info.get("id") else [])
            for entry in entries:
                if not entry:
                    continue
                desc   = (entry.get("description") or entry.get("title") or "").strip()
                vid_id = entry.get("id", "")
                vid_url = entry.get("webpage_url") or entry.get("url") or f"{profile_url}/video/{vid_id}"
                posts.append({
                    "platform": "TikTok",
                    "post_text": desc if desc else "[Video — no caption available without login]",
                    "post_url":  vid_url,
                    "posted_at": str(entry.get("timestamp") or entry.get("upload_date") or ""),
                })
        if posts:
            return posts[:MAX_POSTS]
        return _scrape_tiktok_playwright(handle, profile_url)
    except Exception as e:
        msg = str(e)
        if "secondary user ID" in msg or "blocked" in msg.lower() or "Sign up" in msg:
            return _scrape_tiktok_playwright(handle, profile_url)
        return _err("TikTok", msg[:200], profile_url)


def _scrape_tiktok_playwright(handle: str, profile_url: str) -> list[dict]:
    """Playwright fallback for TikTok when yt-dlp can't extract the profile."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return _err("TikTok",
                    "TikTok blocked yt-dlp access and playwright not installed. "
                    "Run: pip install playwright && playwright install chromium",
                    profile_url)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx_opts: dict = {
                "user_agent": UA,
                "viewport":   {"width": 1280, "height": 900},
                "locale":     "en-US",
            }
            tiktok_cookies = _load_cookies("tiktok.com")
            if tiktok_cookies:
                ctx_opts["storage_state"] = {"cookies": tiktok_cookies, "origins": []}

            ctx  = browser.new_context(**ctx_opts)
            page = ctx.new_page()
            page.route("**/*.{mp4,mp3,webm}", lambda r: r.abort())

            page.goto(profile_url, wait_until="domcontentloaded", timeout=20000)
            time.sleep(2)

            # Dismiss login/signup popups
            for sel in [
                '[data-e2e="modal-close-inner-button"]',
                'button[aria-label="Close"]',
                '[class*="DivCloseContainer"]',
            ]:
                try:
                    btn = page.locator(sel).first
                    if btn.is_visible(timeout=500):
                        btn.click()
                        time.sleep(0.3)
                        break
                except Exception:
                    pass

            seen:       set  = set()
            posts_data: list = []
            stale = 0

            while stale < 2 and len(posts_data) < MAX_POSTS:
                items: list = page.evaluate("""() => {
                    const results = [];
                    const seen = new Set();
                    // Video items on profile page
                    document.querySelectorAll('[data-e2e="user-post-item"]').forEach(item => {
                        const descEl = item.querySelector('[data-e2e="user-post-item-desc"]') ||
                                       item.querySelector('a[title]');
                        const linkEl = item.querySelector('a[href*="/video/"]');
                        const desc = descEl ? (descEl.innerText || descEl.getAttribute('title') || '').trim() : '';
                        const url  = linkEl ? linkEl.href : '';
                        if (url && !seen.has(url)) {
                            seen.add(url);
                            results.push({ text: desc || '[Video]', url });
                        }
                    });
                    return results;
                }""")

                prev = len(posts_data)
                for item in items:
                    if item["url"] not in seen:
                        seen.add(item["url"])
                        posts_data.append({
                            "platform": "TikTok",
                            "post_text": item["text"],
                            "post_url":  item["url"],
                            "posted_at": None,
                        })

                stale = 0 if len(posts_data) > prev else stale + 1
                page.keyboard.press("End")
                time.sleep(1.5)

            browser.close()

            if posts_data:
                return posts_data[:MAX_POSTS]
            return _err("TikTok",
                        "No videos found — profile may be private or TikTok blocked access. "
                        "Run: python tools/scraper_own.py save-cookies",
                        profile_url)
    except Exception as e:
        return _err("TikTok", str(e)[:200], profile_url)


# ── Facebook via Playwright ───────────────────────────────────────────────────

def scrape_facebook_own(handle: str) -> list[dict]:
    page_url = (handle if handle.startswith("http")
                else f"https://www.facebook.com/{handle}")
    clean = handle.rstrip("/").rsplit("/", 1)[-1] if "facebook.com" in handle else handle

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return _err("Facebook", "playwright not installed", page_url)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx_opts: dict = {
                "user_agent": UA,
                "viewport": {"width": 1280, "height": 900},
                "locale": "en-US",
            }
            if _has_cookies("facebook.com"):
                ctx_opts["storage_state"] = {
                    "cookies": _load_cookies("facebook.com"),
                    "origins": [],
                }

            ctx  = browser.new_context(**ctx_opts)
            page = ctx.new_page()
            page.goto(page_url, wait_until="domcontentloaded", timeout=20000)
            time.sleep(2)

            # Dismiss cookie / consent dialogs
            for sel in [
                'div[aria-label="Allow all cookies"] div[role="button"]',
                'div[aria-label="Decline optional cookies"] div[role="button"]',
                '[data-testid="cookie-policy-dialog-accept-button"]',
                'button[title="Allow all cookies"]',
            ]:
                try:
                    btn = page.locator(sel).first
                    if btn.is_visible(timeout=600):
                        btn.click()
                        time.sleep(0.5)
                        break
                except Exception:
                    pass

            seen_texts: set  = set()
            posts_data: list = []
            stale = 0

            while stale < 2 and len(posts_data) < MAX_POSTS:
                # Expand "See more" links so we get full post text
                try:
                    for btn in page.locator('div[role="button"]:has-text("See more")').all():
                        try:
                            btn.click(timeout=400)
                            time.sleep(0.15)
                        except Exception:
                            pass
                except Exception:
                    pass

                # Pull text from every article on the page
                new_texts: list = page.evaluate("""() => {
                    const results = [];
                    const seen = new Set();
                    const SKIP = /^(Like|Comment|Share|Follow|See more|More options|Write a comment)$/i;
                    document.querySelectorAll('[role="article"]').forEach(article => {
                        article.querySelectorAll('[dir="auto"]').forEach(el => {
                            const t = el.innerText?.trim();
                            if (t && t.length > 25 && !seen.has(t) && !SKIP.test(t)) {
                                seen.add(t);
                                results.push(t);
                            }
                        });
                    });
                    return results;
                }""")

                prev = len(posts_data)
                for text in new_texts:
                    if text not in seen_texts:
                        seen_texts.add(text)
                        posts_data.append({
                            "platform": "Facebook",
                            "post_text": text,
                            "post_url":  page_url,
                            "posted_at": None,
                        })

                stale = 0 if len(posts_data) > prev else stale + 1
                page.keyboard.press("End")
                time.sleep(1.5)

            browser.close()

            if posts_data:
                return posts_data[:MAX_POSTS]

            hint = ("" if _has_cookies("facebook.com")
                    else " Run: python tools/scraper_own.py save-cookies")
            return _err("Facebook",
                        f"Facebook shows very limited posts without login.{hint}",
                        page_url)
    except Exception as e:
        return _err("Facebook", str(e)[:200], page_url)


# ── Instagram via instaloader → Playwright ────────────────────────────────────

def scrape_instagram_own(handle: str) -> list[dict]:
    profile_url = f"https://www.instagram.com/{handle}/"

    # Method 1: instaloader (works when Instagram doesn't block)
    try:
        import instaloader
        L = instaloader.Instaloader(
            download_pictures=False, download_videos=False,
            download_video_thumbnails=False, download_geotags=False,
            download_comments=False, save_metadata=False, quiet=True,
            max_connection_attempts=1,  # don't retry — fail fast on 403
        )
        profile = instaloader.Profile.from_username(L.context, handle)
        if profile.is_private:
            return _err("Instagram", f"@{handle} is a private account", profile_url)
        posts = []
        for post in profile.get_posts():
            caption = (post.caption or "").strip()
            posts.append({
                "platform": "Instagram",
                "post_text": caption if caption else "[Photo/Video — no caption]",
                "post_url":  f"https://www.instagram.com/p/{post.shortcode}/",
                "posted_at": str(post.date_utc),
            })
            if len(posts) >= MAX_POSTS:
                break
            time.sleep(0.3)
        if posts:
            return posts
    except Exception:
        pass

    # Method 2: Instagram internal API with sessionid cookie
    if not _has_cookies("instagram.com"):
        return _err("Instagram",
                    "Instagram requires login. Run: python tools/scraper_own.py save-cookies",
                    profile_url)
    return _scrape_instagram_api(handle, profile_url)


def _scrape_instagram_api(handle: str, profile_url: str) -> list[dict]:
    """Use Instagram's internal web API with sessionid cookie — no Playwright needed."""
    cookies = {c["name"]: c["value"] for c in _load_cookies("instagram.com")}
    sessionid = cookies.get("sessionid", "")
    csrftoken  = cookies.get("csrftoken", "")
    if not sessionid:
        return _err("Instagram", "No sessionid cookie — run save-cookies first", profile_url)

    headers = {
        "User-Agent": UA,
        "Accept": "*/*",
        "x-ig-app-id": "936619743392459",
        "x-csrftoken": csrftoken,
        "Referer": f"https://www.instagram.com/{handle}/",
    }
    jar = {c["name"]: c["value"] for c in _load_cookies("instagram.com")}

    try:
        with httpx.Client(headers=headers, cookies=jar, timeout=30) as client:
            # Step 1: get user ID
            r = client.get(
                "https://www.instagram.com/api/v1/users/web_profile_info/",
                params={"username": handle},
            )
            if r.status_code != 200:
                return _err("Instagram", f"Profile API {r.status_code} — profile may be private", profile_url)
            data    = r.json()
            user    = data.get("data", {}).get("user") or {}
            user_id = user.get("id")
            is_priv = user.get("is_private", False)
            if not user_id:
                return _err("Instagram", "User not found", profile_url)
            if is_priv:
                return _err("Instagram", f"@{handle} is a private account", profile_url)

            # Step 2: paginate posts
            posts_data: list = []
            cursor = ""
            while len(posts_data) < MAX_POSTS:
                params: dict = {"count": 12, "user_id": user_id}
                if cursor:
                    params["max_id"] = cursor
                r2 = client.get(
                    "https://www.instagram.com/api/v1/feed/user/{}/".format(user_id),
                    params=params,
                )
                if r2.status_code != 200:
                    break
                feed = r2.json()
                items = feed.get("items") or []
                if not items:
                    break
                for item in items:
                    caption = ((item.get("caption") or {}).get("text") or "").strip()
                    code    = item.get("code") or item.get("id", "")
                    posts_data.append({
                        "platform": "Instagram",
                        "post_text": caption if caption else "[Photo/Video — no caption]",
                        "post_url":  f"https://www.instagram.com/p/{code}/" if code else profile_url,
                        "posted_at": str(item.get("taken_at") or ""),
                    })
                if not feed.get("more_available"):
                    break
                cursor = str(feed.get("next_max_id") or "")
                if not cursor:
                    break

            if posts_data:
                return posts_data[:MAX_POSTS]
            return _err("Instagram", "No posts found on this profile", profile_url)
    except Exception as e:
        return _err("Instagram", str(e)[:200], profile_url)


# ── Twitter/X via official API v2 (free, no cookies needed) ──────────────────

def scrape_twitter_apiv2(handle: str) -> list[dict]:
    """
    Twitter API v2 — NOTE: free tier (402) no longer allows reading tweets.
    Requires $100/month Basic plan. Kept as optional upgrade path.
    Platform uses scrape_twitter_public (Playwright) as the free default.
    """
    import os
    from pathlib import Path
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")

    bearer = os.getenv("TWITTER_BEARER_TOKEN", "")
    profile_url = f"https://x.com/{handle}"
    if not bearer:
        return _err("Twitter/X", "TWITTER_BEARER_TOKEN not set", profile_url)
    headers = {"Authorization": f"Bearer {bearer}"}
    try:
        with httpx.Client(timeout=30) as client:
            r = client.get(
                f"https://api.twitter.com/2/users/by/username/{handle}",
                headers=headers,
                params={"user.fields": "public_metrics"},
            )
            if r.status_code == 402:
                return _err("Twitter/X",
                            "Twitter API free tier no longer supports reading tweets (requires $100/mo Basic plan)",
                            profile_url)
            if r.status_code not in (200,):
                return _err("Twitter/X", f"API error {r.status_code}", profile_url)

            user_id = r.json().get("data", {}).get("id")
            if not user_id:
                return _err("Twitter/X", "User not found", profile_url)

            posts      = []
            next_token = None
            while len(posts) < MAX_POSTS:
                params: dict = {
                    "max_results":  min(100, MAX_POSTS - len(posts)),
                    "tweet.fields": "created_at,text",
                    "exclude":      "retweets",
                }
                if next_token:
                    params["pagination_token"] = next_token
                r2 = client.get(
                    f"https://api.twitter.com/2/users/{user_id}/tweets",
                    headers=headers, params=params)
                if r2.status_code != 200:
                    break
                data   = r2.json()
                tweets = data.get("data", [])
                if not tweets:
                    break
                for t in tweets:
                    posts.append({
                        "platform": "Twitter/X",
                        "post_text": t.get("text", ""),
                        "post_url":  f"https://x.com/{handle}/status/{t['id']}",
                        "posted_at": t.get("created_at"),
                    })
                next_token = data.get("meta", {}).get("next_token")
                if not next_token:
                    break
            return posts[:MAX_POSTS] if posts else _err(
                "Twitter/X", "No public tweets found", profile_url)
    except Exception as e:
        return _err("Twitter/X", str(e)[:200], profile_url)


def scrape_twitter_public(handle: str) -> list[dict]:
    """
    Playwright headless — scrapes public X/Twitter profiles with NO login needed.
    Works for any public account. Uses saved cookies if available for better access.
    This is the free, zero-cost default for the platform.
    """
    profile_url = f"https://x.com/{handle}"
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return _err("Twitter/X",
                    "playwright not installed — run: pip install playwright && playwright install chromium",
                    profile_url)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            ctx_opts: dict = {
                "user_agent": UA,
                "viewport":   {"width": 1280, "height": 900},
                "locale":     "en-US",
            }
            # Use saved cookies if available (better rate limits), but NOT required
            twitter_cookies = _load_cookies("twitter.com") + _load_cookies("x.com")
            if twitter_cookies:
                ctx_opts["storage_state"] = {"cookies": twitter_cookies, "origins": []}

            ctx  = browser.new_context(**ctx_opts)
            page = ctx.new_page()

            # Block images/media to speed up loading
            page.route("**/*.{png,jpg,jpeg,gif,webp,svg,mp4,mp3}", lambda r: r.abort())

            page.goto(profile_url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)

            # Dismiss login prompts if they appear (common on public pages)
            for sel in [
                '[data-testid="sheetDialog"] [aria-label="Close"]',
                '[data-testid="confirmationSheetDialog"] [role="button"]',
                'div[role="button"][aria-label="Close"]',
            ]:
                try:
                    btn = page.locator(sel).first
                    if btn.is_visible(timeout=800):
                        btn.click()
                        time.sleep(0.5)
                        break
                except Exception:
                    pass

            seen:       set  = set()
            posts_data: list = []
            stale = 0

            while stale < 5 and len(posts_data) < MAX_POSTS:
                tweets: list = page.evaluate("""() => {
                    const results = [];
                    document.querySelectorAll('[data-testid="tweet"]').forEach(tw => {
                        const textEl = tw.querySelector('[data-testid="tweetText"]');
                        const text   = textEl ? textEl.innerText.trim() : '';
                        const linkEl = tw.querySelector('a[href*="/status/"]');
                        const url    = linkEl ? 'https://x.com' + linkEl.getAttribute('href') : '';
                        const timeEl = tw.querySelector('time');
                        const ts     = timeEl ? timeEl.getAttribute('datetime') : null;
                        if (text) results.push({ text, url, ts });
                    });
                    return results;
                }""")

                prev = len(posts_data)
                for t in tweets:
                    if t["text"] not in seen:
                        seen.add(t["text"])
                        posts_data.append({
                            "platform": "Twitter/X",
                            "post_text": t["text"],
                            "post_url":  t["url"] or profile_url,
                            "posted_at": t.get("ts"),
                        })

                stale = 0 if len(posts_data) > prev else stale + 1
                page.keyboard.press("End")
                time.sleep(2)

            browser.close()

            if posts_data:
                return posts_data[:MAX_POSTS]
            return _err("Twitter/X",
                        "No tweets found — profile may be protected or suspended",
                        profile_url)
    except Exception as e:
        return _err("Twitter/X", str(e)[:200], profile_url)


# ── Twitter/X via Playwright + cookies ───────────────────────────────────────

def scrape_twitter_own(handle: str) -> list[dict]:
    profile_url = f"https://x.com/{handle}"
    twitter_cookies = _load_cookies("twitter.com") + _load_cookies("x.com")
    if not twitter_cookies:
        return _err("Twitter/X",
                    "Twitter requires login cookies. Run: python tools/scraper_own.py save-cookies",
                    profile_url)
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return _err("Twitter/X", "playwright not installed — run: pip install playwright && playwright install chromium", profile_url)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(
                user_agent=UA,
                viewport={"width": 1280, "height": 900},
                storage_state={"cookies": twitter_cookies, "origins": []},
            )
            page = ctx.new_page()
            page.goto(profile_url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(4)

            # Click "Retry" if Twitter shows its intermittent error state
            for _ in range(3):
                try:
                    retry = page.locator('div[role="button"]:has-text("Retry"), span:has-text("Try again")').first
                    if retry.is_visible(timeout=1500):
                        retry.click()
                        time.sleep(3)
                except Exception:
                    break

            # Wait for tweet feed to actually render
            try:
                page.wait_for_selector('[data-testid="tweet"]', timeout=8000)
            except Exception:
                pass

            seen:       set  = set()
            posts_data: list = []
            stale = 0

            while stale < 5 and len(posts_data) < MAX_POSTS:
                tweets: list = page.evaluate("""() => {
                    const results = [];
                    document.querySelectorAll('[data-testid="tweet"]').forEach(tw => {
                        const textEl = tw.querySelector('[data-testid="tweetText"]');
                        const text   = textEl ? textEl.innerText.trim() : '';
                        const linkEl = tw.querySelector('a[href*="/status/"]');
                        const url    = linkEl ? 'https://x.com' + linkEl.getAttribute('href') : '';
                        const timeEl = tw.querySelector('time');
                        const ts     = timeEl ? timeEl.getAttribute('datetime') : null;
                        if (text) results.push({ text, url, ts });
                    });
                    return results;
                }""")

                prev = len(posts_data)
                for t in tweets:
                    if t["text"] not in seen:
                        seen.add(t["text"])
                        posts_data.append({
                            "platform": "Twitter/X",
                            "post_text": t["text"],
                            "post_url":  t["url"] or profile_url,
                            "posted_at": t.get("ts"),
                        })

                stale = 0 if len(posts_data) > prev else stale + 1
                page.keyboard.press("End")
                time.sleep(2)

            browser.close()
            if posts_data:
                return posts_data[:MAX_POSTS]
            return _err("Twitter/X",
                        "No tweets found — profile may be protected or suspended",
                        profile_url)
    except Exception as e:
        return _err("Twitter/X", str(e)[:200], profile_url)


# ── YouTube via yt-dlp (free, no API key needed) ──────────────────────────────

def scrape_youtube_own(handle: str) -> list[dict]:
    if handle.startswith("http"):
        channel_url = handle
    elif handle.startswith("@"):
        channel_url = f"https://www.youtube.com/{handle}"
    else:
        channel_url = f"https://www.youtube.com/@{handle}"

    try:
        import yt_dlp
    except ImportError:
        return _err("YouTube",
                    "yt-dlp not installed — run: pip install yt-dlp",
                    channel_url)

    netscape = _netscape_cookies_file()
    ydl_opts = {
        "quiet":        True,
        "no_warnings":  True,
        "skip_download": True,
        "extract_flat": True,
        "playlistend":  MAX_POSTS,
        "ignoreerrors": True,
    }
    if netscape:
        ydl_opts["cookiefile"] = netscape

    try:
        posts = []
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(channel_url, download=False)
            if not info or not info.get("entries"):
                info = ydl.extract_info(f"{channel_url}/videos", download=False)
            if not info:
                return _err("YouTube", "Channel not found or no public videos", channel_url)

            for entry in (info.get("entries") or []):
                if not entry:
                    continue
                title = (entry.get("title") or "").strip()
                desc  = (entry.get("description") or "").strip()
                text  = f"{title}. {desc}".strip(". ") if desc else title
                vid_id = entry.get("id") or ""
                posts.append({
                    "platform": "YouTube",
                    "post_text": text if text else "[Video — no title]",
                    "post_url":  (f"https://www.youtube.com/watch?v={vid_id}"
                                  if vid_id else channel_url),
                    "posted_at": str(entry.get("upload_date") or ""),
                })

        if posts:
            return posts[:MAX_POSTS]
        return _err("YouTube", "No videos found on this channel", channel_url)
    except Exception as e:
        return _err("YouTube", str(e)[:200], channel_url)


# ── Cookie saver — run once to enable full scraping ──────────────────────────

def _extract_chrome_cookies(target_domains: list[str]) -> list[dict]:
    """Decrypt Chrome cookies on Windows using DPAPI + AES-GCM (Chrome v80+)."""
    import base64
    import shutil
    import sqlite3
    import tempfile

    try:
        import win32crypt
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ImportError:
        raise RuntimeError("Run: pip install pywin32 cryptography")

    # 1. Read and decrypt the master AES key from Local State
    local_state_path = (
        Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "User Data" / "Local State"
    )
    with open(local_state_path, "r", encoding="utf-8") as f:
        local_state = json.load(f)

    enc_key_b64 = local_state["os_crypt"]["encrypted_key"]
    enc_key     = base64.b64decode(enc_key_b64)[5:]          # strip "DPAPI" prefix
    aes_key     = win32crypt.CryptUnprotectData(enc_key, None, None, None, 0)[1]

    # 2. Copy the Cookies SQLite DB (Chrome locks it while open)
    cookies_db = (
        Path.home() / "AppData" / "Local" / "Google" / "Chrome"
        / "User Data" / "Default" / "Network" / "Cookies"
    )
    if not cookies_db.exists():
        cookies_db = (
            Path.home() / "AppData" / "Local" / "Google" / "Chrome"
            / "User Data" / "Default" / "Cookies"
        )

    tmp_db = Path(tempfile.mktemp(suffix=".db"))
    shutil.copy2(str(cookies_db), str(tmp_db))

    # 3. Query and decrypt
    placeholders = ",".join("?" * len(target_domains))
    like_clauses = " OR ".join("host_key LIKE ?" for _ in target_domains)
    params       = [f"%{d}%" for d in target_domains]

    conn    = sqlite3.connect(str(tmp_db))
    cursor  = conn.cursor()
    cursor.execute(
        f"SELECT host_key, name, encrypted_value, path, is_secure "
        f"FROM cookies WHERE {like_clauses}",
        params,
    )

    results = []
    for host_key, name, enc_val, path, is_secure in cursor.fetchall():
        try:
            if enc_val[:3] in (b"v10", b"v11"):
                nonce  = enc_val[3:15]
                cipher = enc_val[15:]
                value  = AESGCM(aes_key).decrypt(nonce, cipher, None).decode("utf-8")
            else:
                value = win32crypt.CryptUnprotectData(enc_val, None, None, None, 0)[1].decode("utf-8")
            results.append({
                "name":     name,
                "value":    value,
                "domain":   host_key,
                "path":     path,
                "secure":   bool(is_secure),
                "httpOnly": False,
                "sameSite": "Lax",
            })
        except Exception:
            pass

    conn.close()
    tmp_db.unlink(missing_ok=True)
    return results


def save_cookies():
    """
    Import cookies exported from the Cookie-Editor Chrome extension.

    Steps:
      1. Install Cookie-Editor from Chrome Web Store (search "Cookie-Editor")
      2. Go to x.com (while logged in) → click Cookie-Editor → Export → Copy JSON
      3. Run: python tools/scraper_own.py save-cookies x.com
      4. Paste the JSON when prompted, then press Enter twice
      5. Repeat for facebook.com, instagram.com, tiktok.com
    """
    COOKIES_FILE.parent.mkdir(parents=True, exist_ok=True)

    sites = [
        ("Twitter/X",   "x.com",           ["auth_token", "ct0"]),
        ("Facebook",    "facebook.com",     ["c_user", "xs"]),
        ("Instagram",   "instagram.com",    ["sessionid"]),
        ("TikTok",      "tiktok.com",       ["sessionid_ss", "sid_guard", "sid_tt"]),
    ]

    existing: list = []
    if COOKIES_FILE.exists():
        try:
            existing = json.loads(COOKIES_FILE.read_text())
        except Exception:
            existing = []

    print("\n=== Cookie-Editor Import ===")
    print("Install Cookie-Editor extension from Chrome Web Store if you haven't yet.\n")

    all_cookies = list(existing)

    for platform, site, key_cookies in sites:
        print(f"--- {platform} ({site}) ---")
        print(f"  1. Open https://{site} in Chrome (while logged in)")
        print(f"  2. Click the Cookie-Editor extension icon")
        print(f"  3. Click 'Export' → 'Export as JSON' → copy everything")
        print(f"  4. Paste the JSON below, then press Enter twice:\n")

        lines = []
        while True:
            line = input()
            if line == "" and lines:
                break
            lines.append(line)

        raw = "\n".join(lines).strip()
        if not raw:
            print(f"  Skipped {platform}\n")
            continue

        try:
            imported = json.loads(raw)
            # Remove old cookies for this site, add new ones
            all_cookies = [c for c in all_cookies if site not in c.get("domain", "")]
            all_cookies.extend(imported)
            found_keys = [c["name"] for c in imported if c["name"] in key_cookies]
            print(f"  ✓ {platform}: {len(imported)} cookies imported")
            if found_keys:
                print(f"    Auth cookies found: {', '.join(found_keys)}")
            else:
                print(f"    ⚠ Auth cookies NOT found ({', '.join(key_cookies)}) — are you logged in?")
        except Exception as e:
            print(f"  ✗ Invalid JSON: {e}")
        print()

    if not all_cookies:
        print("No cookies saved.")
        return

    COOKIES_FILE.write_text(json.dumps(all_cookies, indent=2))
    print(f"Done! {len(all_cookies)} cookies saved to: {COOKIES_FILE}")
    print("All platforms will now scrape using your Chrome sessions.\n")


def _save_cookies_manual():
    """Fallback: opens a browser window for manual login."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return

    platforms = [
        ("Twitter/X",  "https://x.com/login"),
        ("Facebook",   "https://www.facebook.com/login"),
        ("Instagram",  "https://www.instagram.com/accounts/login"),
        ("TikTok",     "https://www.tiktok.com/login"),
    ]

    print("\nA browser will open — log in to each platform, then press Enter.\n")
    all_cookies: list = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False,
                                    args=["--disable-blink-features=AutomationControlled"])
        ctx = browser.new_context(viewport={"width": 1200, "height": 800})
        for name, url in platforms:
            pg = ctx.new_page()
            pg.goto(url)
            print(f"  [{name}] Log in, then press Enter... ", end="", flush=True)
            input()
            all_cookies.extend(ctx.cookies())
            pg.close()
        browser.close()

    COOKIES_FILE.write_text(json.dumps(all_cookies, indent=2))
    print(f"\nDone. Cookies saved to: {COOKIES_FILE}")


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "save-cookies":
        save_cookies()
    else:
        print("Usage:")
        print("  python tools/scraper_own.py save-cookies   # one-time login setup")
