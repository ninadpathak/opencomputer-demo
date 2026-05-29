# agent.py
import asyncio
import os
from dataclasses import dataclass
import httpx
from opencomputer import Sandbox
from opencomputer.exec import ProcessResult

USE_SNAPSHOT = os.environ.get("USE_SNAPSHOT", "0") == "1"
# Cheaper/faster than Opus for bug-fix-sized tickets. Override with CLAUDE_MODEL.
MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6")

# Base already ships claude/git/node/python; only gh is missing.
RUNTIME_PREP = " && ".join([
    "curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg "
    "| sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg",
    "sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg",
    "echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg]"
    " https://cli.github.com/packages stable main'"
    " | sudo tee /etc/apt/sources.list.d/github-cli.list",
    "sudo apt-get update -qq",
    "sudo apt-get install -y -qq gh",
    "git config --global user.email 'agent@sleep.dev'",
    "git config --global user.name 'sleep-agent'",
    "git config --global init.defaultBranch main",
])


@dataclass
class IssueTask:
    repo: str            # "owner/name"
    issue_number: int
    title: str
    body: str


async def _exec(sandbox, cmd, *, cwd=None, env=None, timeout=60,
                retries=3, check=True) -> ProcessResult:
    """Run a command, retrying transient gateway errors (the platform throws the
    occasional 524). With check=True, a non-zero exit raises with stderr."""
    last = None
    for attempt in range(retries):
        try:
            r = await sandbox.exec.run(cmd, timeout=timeout, cwd=cwd, env=env)
            break
        except (httpx.HTTPStatusError, httpx.ReadTimeout, httpx.RemoteProtocolError) as e:
            last = e
            await asyncio.sleep(4)
    else:
        raise RuntimeError(f"exec failed after {retries} tries: {last}")
    if check and r.exit_code != 0:
        raise RuntimeError(f"`{cmd[:60]}...` exited {r.exit_code}: {r.stderr[:500]}")
    return r


async def run_agent(task: IssueTask) -> str:
    token = os.environ["GITHUB_TOKEN"]
    # Secrets are injected per-command (exec env), NOT via Sandbox.create(envs=).
    # Passing them at create time routes egress through the secrets proxy, which
    # blocks all outbound traffic unless an egress allowlist is configured. Per
    # exec keeps the sandbox on open egress so git/claude/pip just work.
    secret_env = {
        "ANTHROPIC_API_KEY": os.environ["ANTHROPIC_API_KEY"],
        "GITHUB_TOKEN": token,
        "GH_TOKEN": token,
    }
    metadata = {"issue": f"{task.repo}#{task.issue_number}"}

    if USE_SNAPSHOT:
        sandbox = await Sandbox.create(
            snapshot="coder",
            timeout=1800,                                   # 30 min idle ceiling
            metadata=metadata,
        )
    else:
        sandbox = await Sandbox.create(
            template="base",
            timeout=1800,
            metadata=metadata,
        )

    # exec.run is one buffered HTTP call; the SDK's default client timeout (30s)
    # is shorter than a real Claude run, so widen it to the process ceiling.
    sandbox._client._timeout = httpx.Timeout(1700.0)

    try:
        if not USE_SNAPSHOT:
            await _exec(sandbox, RUNTIME_PREP, timeout=300)

        # Clone the repo with a token-authenticated URL
        await _exec(
            sandbox,
            f"git clone https://x-access-token:{token}@github.com/{task.repo}.git repo",
            cwd="/workspace",
            timeout=120,
        )

        branch = f"agent/issue-{task.issue_number}"

        # Write the task so Claude can re-read it when it gets lost mid-loop
        await sandbox.files.write(
            "/workspace/repo/TASK.md",
            "\n".join([
                f"# Issue #{task.issue_number}: {task.title}",
                "",
                task.body or "_(no body)_",
                "",
                "## Working Instructions",
                "",
                "- Read the relevant code before editing.",
                "- Run the project's existing test suite after your changes.",
                "- If tests fail, fix them before stopping.",
                "- Keep the diff focused. Do not refactor unrelated files.",
                "- Delete this TASK.md file before committing.",
            ]),
        )

        await _exec(sandbox, f"git checkout -b {branch}", cwd="/workspace/repo", timeout=30)

        # Hand it to Claude. --dangerously-skip-permissions is safe here because
        # we're in a fresh, disposable VM (and lets it read CLAUDE.md if present).
        # No retry: re-running a non-idempotent agent would double the spend.
        claude_result = await _exec(
            sandbox,
            'claude -p "$(cat TASK.md)" --dangerously-skip-permissions '
            f"--model {MODEL} --max-turns 50 --output-format json",
            cwd="/workspace/repo",
            env=secret_env,
            timeout=1500,
            retries=1,
        )
        if claude_result.exit_code != 0:
            raise RuntimeError(
                f"Claude exited {claude_result.exit_code}: {claude_result.stderr[:500]}"
            )

        safe_title = task.title.replace('"', '\\"')

        # Commit and push. Claude often commits its own work, so only commit when
        # something is actually staged, then always push (a hard `&&` chain here
        # would swallow the push whenever Claude already committed).
        await _exec(
            sandbox,
            "rm -f TASK.md && git add -A && "
            "(git diff --cached --quiet || "
            f'git commit -m "fix: address #{task.issue_number} ({safe_title})") && '
            f"git push --set-upstream origin {branch}",
            cwd="/workspace/repo",
            env=secret_env,
            timeout=120,
        )

        # Open the draft PR
        pr = await _exec(
            sandbox,
            f'gh pr create --draft --title "fix: {safe_title}" '
            f'--body "Closes #{task.issue_number}\n\n'
            '_Drafted by sleep-agent. Review the diff before merging._"',
            cwd="/workspace/repo",
            env=secret_env,
            timeout=60,
        )

        return pr.stdout.strip()
    finally:
        await sandbox.kill()
