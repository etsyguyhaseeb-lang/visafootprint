"""
Analyze scraped social media posts with OpenAI GPT-4o for US visa risk factors.
Input:  posts (list of dicts), person metadata (name, country, reason)
Output: structured risk analysis JSON
"""

import json
import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """You are an expert immigration compliance analyst specializing in US visa social media screening.

Your role is to analyze publicly available social media posts and assess potential risks under US immigration law, specifically:
- INA §212(a)(3): Security and related grounds (terrorism, espionage, sabotage, genocide, Nazi persecution)
- INA §212(a)(2): Criminal and related grounds (controlled substances, prostitution, trafficking)
- INA §212(a)(6): Illegal entrants (alien smuggling support, document fraud)
- General consular officer red flags: anti-American sentiment, calls for violence, extremist affiliations

You must be FAIR, OBJECTIVE, and EVIDENCE-BASED. Only flag content that genuinely poses visa risk.
Normal political opinions, criticism of government policy, immigration advocacy, labor rights, religious expression,
and cultural identity are NOT risk factors. Only flag content that a consular officer would genuinely be concerned about.

Your analysis helps applicants understand their risk profile BEFORE their visa interview so they can address any concerns proactively."""

ANALYSIS_PROMPT_TEMPLATE = """Analyze the following social media posts for US visa risk assessment.

Applicant Information:
- Name: {name}
- Country of Origin: {country}
- Visa Purpose: {reason}

Social Media Posts ({post_count} posts across {platform_count} platform(s)):
{posts_text}

Provide a comprehensive risk analysis in the following JSON format ONLY (no other text):
{{
  "overall_risk": "HIGH" | "MEDIUM" | "LOW",
  "risk_score": <0-100 integer>,
  "scores": {{
    "political": <0-100>,
    "content": <0-100>,
    "network": <0-100>
  }},
  "summary": "<2-3 paragraph professional summary of findings>",
  "flagged_posts": [
    {{
      "text": "<post text excerpt, max 200 chars>",
      "platform": "<platform name>",
      "date": "<date if available or null>",
      "risk_level": "HIGH" | "MEDIUM" | "LOW",
      "risk_category": "<e.g. Political Extremism, Anti-Government Rhetoric, etc>",
      "explanation": "<why this is a risk and what a consular officer would note>"
    }}
  ],
  "network_connections": [
    {{
      "name": "<person's name if identifiable from handle or context, else derive from handle>",
      "handle": "<@handle or username as mentioned in the posts>",
      "platform": "<platform where this person appears>",
      "role": "<their apparent role: e.g. Activist Leader, Family Member, Colleague, Organization>",
      "location": "<city/country if mentioned in posts, else empty string>",
      "post_text": "<their post or the content that reveals this connection, max 160 chars>",
      "posted_at": "<date string if identifiable, else empty string>",
      "risk_factor": "<specific reason this connection raises visa concern>"
    }}
  ],
  "risk_topics": ["<topic1>", "<topic2>"],
  "sentiment": {{
    "positive": <0-100 integer>,
    "neutral": <0-100 integer>,
    "negative": <0-100 integer>
  }},
  "recommendations": [
    "<specific actionable advice for the applicant>",
    "<second recommendation>",
    "<third recommendation>"
  ],
  "overall_assessment": "<one sentence overall verdict>"
}}

Rules:
- risk_score 0-30 = LOW, 31-60 = MEDIUM, 61-100 = HIGH
- Only include genuinely concerning posts in flagged_posts (max 10)
- network_connections: only populate when posts contain real mentions of concerning individuals/organizations (max 6); use empty array [] when no concerning connections found
- sentiment percentages must sum to 100
- scores.political, scores.content, scores.network are independent sub-scores
- Be fair: most normal people have LOW risk"""


def analyze_posts(
    posts: list[dict],
    name: str,
    country: str,
    reason: str,
) -> dict:
    if not posts:
        return _empty_result()

    # Filter out scrape errors, keep real posts
    real_posts = [p for p in posts if not p.get("post_text", "").startswith("[SCRAPE_ERROR")]
    error_posts = [p for p in posts if p.get("post_text", "").startswith("[SCRAPE_ERROR")]

    if not real_posts:
        result = _empty_result()
        result["summary"] = (
            "Unable to retrieve posts from the provided social media accounts. "
            "This may be due to private profiles, platform restrictions, or invalid handles. "
            "Please verify the account handles and ensure profiles are set to public."
        )
        result["scrape_errors"] = [p["post_text"] for p in error_posts]
        return result

    # Format posts for prompt
    posts_text = "\n\n".join(
        f"[{i+1}] Platform: {p.get('platform','Unknown')} | "
        f"Date: {p.get('posted_at') or 'Unknown'}\n{p.get('post_text','')}"
        for i, p in enumerate(real_posts[:500])  # match scraper MAX_POSTS
    )

    platforms = {p.get("platform", "Unknown") for p in real_posts}

    prompt = ANALYSIS_PROMPT_TEMPLATE.format(
        name=name,
        country=country,
        reason=reason,
        post_count=len(real_posts),
        platform_count=len(platforms),
        posts_text=posts_text,
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
            max_tokens=8000,
        )
    except Exception as _oa_err:
        print(f"[OPENAI ERROR] {type(_oa_err).__name__}: {_oa_err}", flush=True)
        raise

    raw = response.choices[0].message.content
    result = json.loads(raw)

    # Attach metadata
    result["posts_analyzed"] = len(real_posts)
    result["platforms_analyzed"] = list(platforms)
    if error_posts:
        result["scrape_errors"] = [p["post_text"] for p in error_posts]

    return result


def _empty_result() -> dict:
    return {
        "overall_risk": "LOW",
        "risk_score": 0,
        "scores": {"political": 0, "content": 0, "network": 0},
        "summary": "No posts available for analysis.",
        "flagged_posts": [],
        "network_connections": [],
        "risk_topics": [],
        "sentiment": {"positive": 50, "neutral": 40, "negative": 10},
        "recommendations": ["Ensure your social media profiles are set to public for accurate screening."],
        "overall_assessment": "Insufficient data for analysis.",
        "posts_analyzed": 0,
        "platforms_analyzed": [],
    }


if __name__ == "__main__":
    # Quick test with sample posts
    sample_posts = [
        {"platform": "Twitter/X", "post_text": "Excited to visit the US next year! Can't wait to see NYC.", "post_url": "", "posted_at": None},
        {"platform": "Instagram", "post_text": "Beautiful sunset from my trip to London. #travel #wanderlust", "post_url": "", "posted_at": None},
    ]
    result = analyze_posts(sample_posts, "Test User", "India", "Tourism")
    print(json.dumps(result, indent=2))
