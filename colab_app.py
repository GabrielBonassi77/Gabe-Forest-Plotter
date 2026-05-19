from __future__ import annotations

import re
import subprocess
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent
LOG_PATH = ROOT / "cloudflared.log"


def run_background(command: list[str], log_file: Path | None = None) -> subprocess.Popen:
    if log_file is None:
        return subprocess.Popen(command, cwd=ROOT)

    handle = log_file.open("w", encoding="utf-8")
    return subprocess.Popen(
        command,
        cwd=ROOT,
        stdout=handle,
        stderr=subprocess.STDOUT,
        text=True,
    )


def wait_for_tunnel_url(timeout_seconds: int = 45) -> str:
    pattern = re.compile(r"https://[a-zA-Z0-9.-]+\\.trycloudflare\\.com")
    deadline = time.time() + timeout_seconds

    while time.time() < deadline:
        if LOG_PATH.exists():
            text = LOG_PATH.read_text(encoding="utf-8", errors="ignore")
            match = pattern.search(text)
            if match:
                return match.group(0)
        time.sleep(1)

    raise RuntimeError(
        "Could not find the Cloudflare tunnel URL. "
        "Open cloudflared.log in the Colab file browser to inspect the tunnel output."
    )


def main() -> None:
    run_background(
        [
            "streamlit",
            "run",
            "app.py",
            "--server.port",
            "8501",
            "--server.headless",
            "true",
            "--browser.gatherUsageStats",
            "false",
        ]
    )
    time.sleep(5)

    run_background(
        ["cloudflared", "tunnel", "--url", "http://localhost:8501"],
        log_file=LOG_PATH,
    )

    url = wait_for_tunnel_url()
    print("\nForest Plotter is running.")
    print(f"Open this link: {url}\n")


if __name__ == "__main__":
    main()
