# build_snapshot.py
import asyncio
import sys
from opencomputer import Snapshots, Image
from dotenv import load_dotenv

load_dotenv()


async def main() -> None:
    snapshots = Snapshots()

    image = (
        Image.base()
        .apt_install(["curl", "git", "jq", "build-essential", "ca-certificates"])
        .run_commands(
            # gh CLI from the official apt repo (build runs as non-root, so sudo)
            "curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg "
            "| sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg",
            "sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg",
            "echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg]"
            " https://cli.github.com/packages stable main'"
            " | sudo tee /etc/apt/sources.list.d/github-cli.list",
            "sudo apt update && sudo apt install -y gh",
            "sudo npm install -g @anthropic-ai/claude-code",
            "git config --global user.email 'agent@sleep.dev'",
            "git config --global user.name 'sleep-agent'",
            "git config --global init.defaultBranch main",
        )
        .workdir("/workspace")
    )

    snap = await snapshots.create(
        name="coder",
        image=image,
        on_build_logs=lambda line: sys.stdout.write(line),
    )
    print(f"\nSnapshot ready: {snap['name']} ({snap['id']})")


if __name__ == "__main__":
    asyncio.run(main())
