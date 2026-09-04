import os
import socket
import sys
import threading
import time
import urllib.request
from pathlib import Path

from streamlit.web import bootstrap
import webview


def free_port():
    with socket.socket() as socket_instance:
        socket_instance.bind(("127.0.0.1", 0))
        return socket_instance.getsockname()[1]


def local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as socket_instance:
            socket_instance.connect(("8.8.8.8", 80))
            return socket_instance.getsockname()[0]
    except OSError:
        return "127.0.0.1"


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
    os.environ.setdefault("PICXELLENS_PUBLIC_URL", f"http://{local_ip()}:{port}")
    server_options = {"server.headless": True, "server.address": "127.0.0.1", "server.port": port}
    server_thread = threading.Thread(
        target=bootstrap.run,
        args=(str(dashboard_path()), "", [], server_options),
        daemon=True,
    )
    server_thread.start()
    try:
        threading.Thread(target=wait_for_server, args=(url,), daemon=True).start()
        time.sleep(3)
        webview.create_window("picxellens staff desk", url, width=1280, height=820, min_size=(960, 640))
        webview.start()
    finally:
        os._exit(0)


if __name__ == "__main__":
    main()