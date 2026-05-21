from __future__ import annotations

import re
import shutil
import subprocess
import sys
import time
from urllib.request import urlopen
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CLOUDFLARED_LOG_PATH = ROOT / "cloudflared.log"
STREAMLIT_LOG_PATH = ROOT / "streamlit.log"


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


def wait_for_streamlit(timeout_seconds: int = 45) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            with urlopen("http://localhost:8501", timeout=2):
                return
        except Exception:
            time.sleep(1)
    raise RuntimeError("Streamlit did not start on http://localhost:8501. Check streamlit.log.")


def wait_for_tunnel_url(timeout_seconds: int = 90) -> str:
    pattern = re.compile(r"https://[a-zA-Z0-9.-]+\.trycloudflare\.com")
    deadline = time.time() + timeout_seconds

    while time.time() < deadline:
        if CLOUDFLARED_LOG_PATH.exists():
            text = CLOUDFLARED_LOG_PATH.read_text(encoding="utf-8", errors="ignore")
            match = pattern.search(text)
            if match:
                return match.group(0)
        time.sleep(1)

    log_tail = ""
    if CLOUDFLARED_LOG_PATH.exists():
        log_tail = CLOUDFLARED_LOG_PATH.read_text(encoding="utf-8", errors="ignore")[-1200:]
    raise RuntimeError(
        "Could not find the Cloudflare tunnel URL. "
        "Open cloudflared.log in the Colab file browser to inspect the tunnel output.\n\n"
        f"cloudflared.log tail:\n{log_tail}"
    )


def main() -> None:
    if shutil.which("cloudflared") is None:
        raise RuntimeError("cloudflared is not installed. Run the install cell before launching the app.")

    run_background(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "app.py",
            "--server.port",
            "8501",
            "--server.headless",
            "true",
            "--browser.gatherUsageStats",
            "false",
        ],
        log_file=STREAMLIT_LOG_PATH,
    )
    wait_for_streamlit()

    run_background(
        ["cloudflared", "tunnel", "--url", "http://localhost:8501"],
        log_file=CLOUDFLARED_LOG_PATH,
    )

    url = wait_for_tunnel_url()
    print("\nForest Plotter is running.")
    print(f"Open this link: {url}\n")


if __name__ == "__main__":
    main()
