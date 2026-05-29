# run_once.py — trigger the agent on a single issue without the webhook.
#
#   python run_once.py <owner/repo> <issue_number>
#
# Reads the issue from GitHub, runs the agent, prints the draft PR URL.
import asyncio
import os
import sys
import httpx
from dotenv import load_dotenv
from agent import IssueTask, run_agent

load_dotenv()


async def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("usage: python run_once.py <owner/repo> <issue_number>")
    repo, issue_number = sys.argv[1], int(sys.argv[2])
    token = os.environ["GITHUB_TOKEN"]

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            f"https://api.github.com/repos/{repo}/issues/{issue_number}",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        r.raise_for_status()
        issue = r.json()

    task = IssueTask(
        repo=repo,
        issue_number=issue_number,
        title=issue["title"],
        body=issue.get("body") or "",
    )
    print(f"→ running agent on {repo}#{issue_number}: {task.title!r}")
    pr_url = await run_agent(task)
    print(f"\n✅ Draft PR: {pr_url}")


if __name__ == "__main__":
    asyncio.run(main())
