import os
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

import webview


def free_port():
    with socket.socket() as socket_instance:
        socket_instance.bind(("127.0.0.1", 0))
        return socket_instance.getsockname()[1]


def dashboard_path():
    bundle_root = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    return bundle_root / "Dashboard.py"


def wait_for_server(url):
    for _ in range(80):
        try:
            urllib.request.urlopen(url, timeout=1)
            return
        except Exception:
            time.sleep(0.25)


def main():
    port = free_port()
    url = f"http://127.0.0.1:{port}/?view=staff"
    environment = os.environ.copy()
    environment["PICXELLENS_PUBLIC_URL"] = environment.get("PICXELLENS_PUBLIC_URL", "http://localhost:8501")
    server = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", str(dashboard_path()), "--server.headless=true", "--server.address=127.0.0.1", f"--server.port={port}"],
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        threading.Thread(target=wait_for_server, args=(url,), daemon=True).start()
        time.sleep(2)
        webview.create_window("picxellens staff desk", url, width=1280, height=820, min_size=(960, 640))
        webview.start()
    finally:
        server.terminate()
        server.wait(timeout=5)


if __name__ == "__main__":
    main()