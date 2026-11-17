#!/usr/bin/env python3
"""
HodgeGuard Lead Radar v3.0
- Title-scoped GitHub issue search across AI Coding Agent repos (zero noise)
- Hacker News Algolia story + comment search for token burn / agent loop pain points
"""

import json
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

AGENT_REPOS = [
    "sst/opencode",
    "anthropics/claude-code",
    "cline/cline",
    "RooVetGit/Roo-Code",
    "Aider-AI/aider",
    "continuedev/continue",
]

TITLE_KEYWORDS = [
    "loop",
    "repeating",
    "burns tokens",
    "usage",
    "retry",
]


def search_github_titles():
    print("\n=== 🎯 TITLE-MATCHED AI AGENT ISSUES (LAST 30 DAYS) ===")
    since_date = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
    repo_filter = " ".join(f"repo:{r}" for r in AGENT_REPOS)
    seen = set()

    for kw in TITLE_KEYWORDS:
        full_q = f"{kw} in:title {repo_filter} is:issue created:>={since_date}"
        url = (
            f"https://api.github.com/search/issues?"
            f"q={urllib.parse.quote(full_q)}&sort=created&order=desc&per_page=8"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "HodgeGuard-Radar/3.0"})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for item in data.get("items", []):
                    html_url = item.get("html_url", "")
                    if html_url in seen:
                        continue
                    seen.add(html_url)
                    repo_name = html_url.split("github.com/")[1].split("/issues/")[0]
                    title = item.get("title", "")
                    created = item.get("created_at", "")[:10]
                    print(f"[{created}] [{repo_name}] {title}\n   👉 {html_url}")
        except Exception as e:
            print(f"GitHub query error ({kw}): {e}")


def search_hn_discussions():
    print("\n=== 🟧 HACKER NEWS STORIES & COMMENTS (TOKEN BURN / AGENT LOOPS) ===")
    queries = [
        ("story", "claude code tokens"),
        ("story", "coding agent loop"),
        ("comment", "claude code stuck in a loop"),
        ("comment", "cursor infinite loop"),
        ("comment", "opencode loop"),
    ]
    seen = set()
    since_ts = int((datetime.now(timezone.utc) - timedelta(days=21)).timestamp())

    for tag, q in queries:
        url = (
            f"https://hn.algolia.com/api/v1/search_by_date?"
            f"query={urllib.parse.quote(q)}&tags={tag}&numericFilters=created_at_i>{since_ts}&hitsPerPage=5"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "HodgeGuard-Radar/3.0"})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for hit in data.get("hits", []):
                    obj_id = hit.get("objectID")
                    if not obj_id or obj_id in seen:
                        continue
                    seen.add(obj_id)
                    title = hit.get("title") or hit.get("story_title") or "HN Thread"
                    created = (hit.get("created_at") or "")[:10]
                    hn_url = f"https://news.ycombinator.com/item?id={obj_id}"
                    print(f"[{created}] [{tag.upper()}] {title}\n   👉 {hn_url}")
        except Exception as e:
            print(f"HN query error ({q}): {e}")


if __name__ == "__main__":
    print("Running HodgeGuard Lead Radar v3.0...")
    search_github_titles()
    search_hn_discussions()
