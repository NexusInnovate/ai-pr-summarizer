from fastapi import FastAPI, Request, Header, HTTPException
import hmac
import hashlib
import os
import json
import httpx

from github_utils import get_diff
from ai_summarizer import review_pr

from dotenv import load_dotenv
load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")

app = FastAPI()


@app.post("/pr-reviewer-webhook")
async def pr_reviewer_webhook(request: Request, x_hub_signature_256: str = Header(None)):
    body = await request.body()

    # Verify GitHub signature
    mac = hmac.new(WEBHOOK_SECRET.encode(), msg=body, digestmod=hashlib.sha256)
    expected_signature = f"sha256={mac.hexdigest()}"
    if not hmac.compare_digest(expected_signature, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = json.loads(body)

    if payload.get("action") not in ["opened", "synchronize"]:
        return {"status": "ignored"}

    pr = payload["pull_request"]
    repo = payload["repository"]["full_name"]
    pr_number = pr["number"]
    title = pr["title"]
    author = pr["user"]["login"]
    comments_url = pr["comments_url"]

    # Get PR diff
    diff_text = get_diff(repo, pr_number, GITHUB_TOKEN)

    # Run AI code review
    suggestions = review_pr(diff_text)

    # Post comment back to PR
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    comment_body = {
        "body": f"🤖 **AI Code Review Suggestions for #{pr_number} - {title}**\n\n"
                f"👤 Author: `{author}`\n\n"
                f"---\n\n"
                f"{suggestions}"
    }

    async with httpx.AsyncClient() as client:
        await client.post(comments_url, headers=headers, json=comment_body)

    return {"status": "success"}
@app.get("/health")
async def pr_reviewer_webhook(request: Request):
    return {"status": "Good"}
