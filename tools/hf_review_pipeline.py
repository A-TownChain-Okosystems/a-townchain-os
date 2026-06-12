"""
A-TownChain OS — HuggingFace Code Review Pipeline
Automated AI-powered code review using HuggingFace Inference API.
Issue: #50 | Wiki: Kap. 61

Usage:
  python tools/hf_review_pipeline.py --file blockchain/consensus/hybrid_consensus.py
  python tools/hf_review_pipeline.py --pr 51
"""
import os
import sys
import json
import argparse
import requests
import logging
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger("hf_pipeline")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

HF_TOKEN     = os.environ.get("HUGGING_FACE_ACCESS_TOKEN", "")
GITHUB_TOKEN = os.environ.get("GITHUB_ACCESS_TOKEN", "")
HF_MODEL     = "google/gemma-2-2b-it"
HF_API_URL   = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
CODE_REPO    = "A-TownChain-Okosystems/a-townchain-os"
MAX_FILE_BYTES = 4000  # trim large files for the prompt

GH_HEADERS = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
HF_HEADERS = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}


def review_code(code: str, filename: str = "") -> str:
    """Send code to HuggingFace for review."""
    prompt = (
        f"You are a senior Python/blockchain developer. "
        f"Review the following code from {filename or 'unknown file'}. "
        "Identify: bugs, security issues, missing edge cases, improvements. "
        "Be concise. Output as numbered list.\n\n"
        f"```python\n{code[:MAX_FILE_BYTES]}\n```\n\nCode Review:"
    )
    try:
        r = requests.post(HF_API_URL, headers=HF_HEADERS,
                          json={"inputs": prompt, "parameters": {"max_new_tokens": 512, "temperature": 0.3}},
                          timeout=60)
        if r.status_code == 200:
            data = r.json()
            return data[0]["generated_text"] if isinstance(data, list) else str(data)
        return f"HF API error: {r.status_code} — {r.text[:100]}"
    except Exception as e:
        return f"Review failed: {e}"


def get_pr_files(pr_number: int) -> List[Dict]:
    """Fetch changed files in a GitHub PR."""
    url = f"https://api.github.com/repos/{CODE_REPO}/pulls/{pr_number}/files"
    r = requests.get(url, headers=GH_HEADERS, timeout=10).json()
    return r if isinstance(r, list) else []


def get_file_content(path: str) -> Optional[str]:
    """Fetch file content from GitHub."""
    import base64
    url = f"https://api.github.com/repos/{CODE_REPO}/contents/{path}"
    r = requests.get(url, headers=GH_HEADERS, timeout=10).json()
    if "content" in r:
        return base64.b64decode(r["content"]).decode(errors="ignore")
    return None


def post_pr_comment(pr_number: int, body: str) -> bool:
    """Post review comment to a GitHub PR."""
    url = f"https://api.github.com/repos/{CODE_REPO}/issues/{pr_number}/comments"
    r = requests.post(url, headers={**GH_HEADERS, "Content-Type": "application/json"},
                      json={"body": body}, timeout=10)
    return r.status_code in (200, 201)


def run_review(args):
    results = []

    if args.file:
        path = args.file
        content = get_file_content(path)
        if content:
            logger.info(f"Reviewing: {path}")
            review = review_code(content, path)
            results.append({"file": path, "review": review})
            print(f"\n=== {path} ===\n{review}\n")
        else:
            logger.error(f"Could not fetch: {path}")

    elif args.pr:
        pr = int(args.pr)
        files = get_pr_files(pr)
        py_files = [f for f in files if f.get("filename","").endswith(".py")]
        logger.info(f"PR #{pr}: {len(py_files)} Python files to review")

        comment_parts = [f"## 🤖 Aurora AI Code Review — PR #{pr}\n"]
        for f in py_files[:5]:  # limit to 5 files per PR
            path = f["filename"]
            content = get_file_content(path)
            if not content:
                continue
            logger.info(f"  Reviewing: {path}")
            review = review_code(content, path)
            results.append({"file": path, "review": review})
            comment_parts.append(f"### `{path}`\n{review}\n")

        comment = "\n".join(comment_parts)
        if args.post and GITHUB_TOKEN:
            ok = post_pr_comment(pr, comment)
            logger.info(f"Comment posted: {ok}")
        else:
            print(comment)

    # Save report
    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        logger.info(f"Report saved: {args.output}")

    return results


def main():
    parser = argparse.ArgumentParser(description="HuggingFace Code Review Pipeline")
    parser.add_argument("--file", help="Review a single file")
    parser.add_argument("--pr",   help="Review all changed files in a PR")
    parser.add_argument("--post", action="store_true", help="Post review as GitHub comment")
    parser.add_argument("--output", help="Save report to JSON file")
    args = parser.parse_args()

    if not args.file and not args.pr:
        parser.print_help()
        sys.exit(1)

    if not HF_TOKEN:
        logger.warning("No HUGGING_FACE_ACCESS_TOKEN set — requests may be rate-limited")

    run_review(args)


if __name__ == "__main__":
    main()
