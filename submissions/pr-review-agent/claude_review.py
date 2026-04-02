#!/usr/bin/env python3
"""
Claude Code PR Review Agent
Usage: python3 claude_review.py --pr https://github.com/owner/repo/pull/123
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path


ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")


def get_pr_diff(pr_url: str) -> tuple[str, dict]:
    """Fetch PR diff and metadata from GitHub API."""
    m = re.match(r'https://github\.com/([^/]+)/([^/]+)/pull/(\d+)', pr_url)
    if not m:
        raise ValueError(f"Invalid PR URL: {pr_url}")
    owner, repo, pr_num = m.groups()

    headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "claude-review"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    # Get PR metadata
    meta_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_num}"
    req = urllib.request.Request(meta_url, headers=headers)
    with urllib.request.urlopen(req) as r:
        meta = json.loads(r.read())

    # Get diff
    diff_headers = {**headers, "Accept": "application/vnd.github.v3.diff"}
    req = urllib.request.Request(meta_url, headers=diff_headers)
    with urllib.request.urlopen(req) as r:
        diff = r.read().decode("utf-8", errors="replace")

    return diff[:12000], meta  # cap at 12k chars


def review_with_claude(diff: str, pr_title: str, pr_body: str) -> str:
    """Call Claude API to generate structured review."""
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY not set")

    prompt = f"""You are an expert code reviewer. Review this PR and return a structured Markdown comment.

PR Title: {pr_title}
PR Description: {pr_body[:500] if pr_body else 'No description'}

Diff:
```diff
{diff}
```

Return ONLY this exact Markdown structure, no preamble:

## 📋 Summary
[2-3 sentence summary of what this PR does]

## ⚠️ Identified Risks
- [risk 1]
- [risk 2 or "None identified"]

## 💡 Improvement Suggestions
- [suggestion 1]
- [suggestion 2 or "Looks good as-is"]

## 🎯 Confidence Score
[Low / Medium / High] — [one sentence explanation]"""

    payload = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01"
        }
    )
    with urllib.request.urlopen(req) as r:
        result = json.loads(r.read())

    return result["content"][0]["text"]


def post_github_comment(pr_url: str, comment: str):
    """Post review comment to GitHub PR."""
    m = re.match(r'https://github\.com/([^/]+)/([^/]+)/pull/(\d+)', pr_url)
    owner, repo, pr_num = m.groups()

    if not GITHUB_TOKEN:
        print("⚠️  GITHUB_TOKEN not set — skipping auto-post to GitHub")
        return

    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_num}/comments"
    payload = json.dumps({"body": comment}).encode()
    req = urllib.request.Request(url, data=payload, headers={
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
        "User-Agent": "claude-review"
    })
    with urllib.request.urlopen(req) as r:
        result = json.loads(r.read())
    print(f"✅ Comment posted: {result['html_url']}")


def main():
    parser = argparse.ArgumentParser(description="Claude Code PR Review Agent")
    parser.add_argument("--pr", required=True, help="GitHub PR URL")
    parser.add_argument("--post", action="store_true", help="Post comment to GitHub")
    parser.add_argument("--output", help="Save review to file")
    args = parser.parse_args()

    print(f"🔍 Fetching PR: {args.pr}")
    diff, meta = get_pr_diff(args.pr)
    print(f"📄 Got diff ({len(diff)} chars) for: {meta['title']}")

    print("🤖 Reviewing with Claude...")
    review = review_with_claude(diff, meta["title"], meta.get("body", ""))

    print("\n" + "="*60)
    print(review)
    print("="*60 + "\n")

    if args.output:
        Path(args.output).write_text(review)
        print(f"💾 Saved to {args.output}")

    if args.post:
        post_github_comment(args.pr, review)


if __name__ == "__main__":
    main()
