# server.py
import asyncio
import hashlib
import hmac
import os
import httpx
from fastapi import FastAPI, Header, HTTPException, Request
from dotenv import load_dotenv
from agent import IssueTask, run_agent

load_dotenv()

WEBHOOK_SECRET = os.environ["GITHUB_WEBHOOK_SECRET"].encode()
GH_TOKEN = os.environ["GITHUB_TOKEN"]
GH_API = "https://api.github.com"
GH_HEADERS = {
    "Authorization": f"Bearer {GH_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

app = FastAPI()


def verify_signature(body: bytes, signature: str) -> bool:
    expected = "sha256=" + hmac.new(WEBHOOK_SECRET, body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


async def post_comment(repo: str, issue_number: int, body: str) -> None:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{GH_API}/repos/{repo}/issues/{issue_number}/comments",
            headers=GH_HEADERS,
            json={"body": body},
        )
        r.raise_for_status()


async def handle_labeled(payload: dict) -> None:
    repo = payload["repository"]["full_name"]
    issue_number = payload["issue"]["number"]
    task = IssueTask(
        repo=repo,
        issue_number=issue_number,
        title=payload["issue"]["title"],
        body=payload["issue"].get("body") or "",
    )

    await post_comment(repo, issue_number, "🛌 sleep-agent picked this up. Draft PR incoming.")

    try:
        pr_url = await run_agent(task)
        await post_comment(repo, issue_number, f"✅ Draft PR ready: {pr_url}")
    except Exception as exc:
        await post_comment(
            repo, issue_number,
            f"❌ sleep-agent failed:\n\n```\n{exc}\n```",
        )


@app.post("/webhook")
async def webhook(
    request: Request,
    x_hub_signature_256: str = Header(default=""),
    x_github_event: str = Header(default=""),
):
    body = await request.body()
    if not verify_signature(body, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="bad signature")

    if x_github_event != "issues":
        return {"status": "ignored"}

    payload = await request.json()
    if payload.get("action") != "labeled":
        return {"status": "ignored"}
    if (payload.get("label") or {}).get("name") != "agent":
        return {"status": "ignored"}

    # Fire-and-forget. Don't block the webhook response on the agent run.
    asyncio.create_task(handle_labeled(payload))
    return {"status": "accepted"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "3000")))
