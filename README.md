# sleep-agent — a self-hosted background coding agent

Label a GitHub issue with `agent`, and a disposable [OpenComputer](https://opencomputer.dev)
sandbox boots, runs Claude Code headless on the issue, and opens a draft PR.

Full write-up: **Build a Background Coding Agent that Works While You Sleep**.

## Files

| File | What it does |
|------|--------------|
| `build_snapshot.py` | One-time: bakes a `coder` snapshot with `gh` + Claude Code pre-installed. Optional. |
| `agent.py` | Handles one issue: boots a sandbox, clones the repo, runs Claude Code, opens the draft PR. |
| `server.py` | FastAPI webhook receiver. Fires `run_agent` when an issue is labeled `agent`. |
| `run_once.py` | Trigger the agent on one issue directly, without the webhook. |

## Setup

```sh
pip install opencomputer-sdk fastapi "uvicorn[standard]" httpx python-dotenv
cp .env.example .env   # then fill in your keys
```

Keys (`.env`):

- `OPENCOMPUTER_API_KEY` — app.opencomputer.dev → API Keys
- `ANTHROPIC_API_KEY` — console.anthropic.com → API Keys (Claude Code access)
- `GITHUB_TOKEN` — github.com/settings/tokens, `repo` scope
- `GITHUB_WEBHOOK_SECRET` — any random string; paste the same value into the GitHub webhook

Optional: `USE_SNAPSHOT=1` boots the pre-baked snapshot (run `build_snapshot.py` first);
`CLAUDE_MODEL` overrides the model (default `claude-sonnet-4-6`).

## Run

Direct, one issue (no webhook):

```sh
python run_once.py <owner/repo> <issue_number>
```

Full webhook flow:

```sh
python server.py                 # listens on $PORT (default 3000)
ngrok http 3000                  # or expose via an OpenComputer preview URL
```

Then add a GitHub webhook pointing at `<public-url>/webhook` (content type `application/json`,
the same secret, **Issues** events only), and create an `agent` label. Label an issue and wait
for the draft PR.

> Each run uses `--dangerously-skip-permissions`, which is safe only because every run is in a
> fresh, disposable VM. Don't run that flag on your own machine.
