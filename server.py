import json
import os
import socket
import sys
from io import BytesIO
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import qrcode

ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
DEFAULT_DATA_DIR = Path(sys.executable).parent if getattr(sys, "frozen", False) else ROOT
DATA_DIR = Path(os.environ.get("PIXCELLENS_DATA_DIR", DEFAULT_DATA_DIR))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATABASE = DATA_DIR / "registrations.json"
SCHOOLS_DATABASE = DATA_DIR / "schools.json"
try:
    TIME_ZONE = ZoneInfo(os.environ.get("PIXCELLENS_TIME_ZONE", "Asia/Manila"))
except ZoneInfoNotFoundError:
    TIME_ZONE = timezone(timedelta(hours=8), name="Asia/Manila")


def read_records():
    if not DATABASE.exists():
        return []
    records = json.loads(DATABASE.read_text(encoding="utf-8"))
    changed = False
    for record in records:
        if record.get("_time_zone") == "Asia/Manila":
            continue
        try:
            old_time = datetime.strptime(record["time"], "%I:%M %p")
            record["time"] = (old_time + timedelta(hours=8)).strftime("%I:%M %p")
        except (KeyError, TypeError, ValueError):
            pass
        record["_time_zone"] = "Asia/Manila"
        changed = True
    if changed:
        write_records(records)
    return records


def write_records(records):
    temporary = DATABASE.with_suffix(".tmp")
    temporary.write_text(json.dumps(records, indent=2), encoding="utf-8")
    temporary.replace(DATABASE)


def read_schools():
    if not SCHOOLS_DATABASE.exists():
        return ["Davao State University", "Ateneo de Davao", "UM Davao"]
    return json.loads(SCHOOLS_DATABASE.read_text(encoding="utf-8"))


def write_schools(schools):
    temporary = SCHOOLS_DATABASE.with_suffix(".tmp")
    temporary.write_text(json.dumps(sorted(set(schools)), indent=2), encoding="utf-8")
    temporary.replace(SCHOOLS_DATABASE)


class OfficeHandler(BaseHTTPRequestHandler):
    def send_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/health":
            self.send_json({"status": "ok"})
            return
        if path == "/api/qr":
            target = parse_qs(parsed.query).get("data", [""])[0]
            if not target:
                self.send_error(400, "QR data is required")
                return
            image = BytesIO()
            qrcode.make(target).save(image, format="PNG")
            body = image.getvalue()
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Cache-Control", "public, max-age=3600")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if path == "/api/registrations":
            self.send_json(read_records())
            return
        if path == "/api/schools":
            self.send_json(read_schools())
            return
        file_path = ROOT / ("index.html" if path == "/" else path.lstrip("/"))
        if file_path.is_file() and ROOT in file_path.parents:
            content_type = {".html": "text/html", ".css": "text/css", ".js": "text/javascript"}.get(file_path.suffix, "application/octet-stream")
            body = file_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_error(404)

    def do_POST(self):
        if self.path == "/api/schools":
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length))
            school = data.get("name", "").strip()
            if not school:
                self.send_error(400, "School name is required")
                return
            schools = read_schools()
            if school not in schools:
                schools.append(school)
                write_schools(schools)
            self.send_json(read_schools(), 201)
            return
        if self.path != "/api/registrations":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", 0))
        data = json.loads(self.rfile.read(length))
        records = read_records()
        next_number = max([int(record["queue"]) for record in records] or [100]) + 1
        record = {**data, "id": next_number, "queue": str(next_number).zfill(3), "time": datetime.now(TIME_ZONE).strftime("%I:%M %p"), "_time_zone": "Asia/Manila", "status": "Waiting"}
        records.append(record)
        write_records(records)
        self.send_json(record, 201)

    def do_PATCH(self):
        parts = self.path.strip("/").split("/")
        if len(parts) != 3 or parts[:2] != ["api", "registrations"]:
            self.send_error(404)
            return
        record_id = int(parts[2])
        length = int(self.headers.get("Content-Length", 0))
        data = json.loads(self.rfile.read(length)) if length else {}
        records = read_records()
        for record in records:
            if record["id"] == record_id:
                record["status"] = data.get("status", "Done")
                write_records(records)
                self.send_json(record)
                return
        self.send_error(404)

    def do_DELETE(self):
        parts = self.path.strip("/").split("/")
        if len(parts) == 3 and parts[:2] == ["api", "registrations"] and parts[2] != "done":
            record_id = int(parts[2])
            records = [record for record in read_records() if record["id"] != record_id]
            write_records(records)
            self.send_json(records)
            return
        if self.path != "/api/registrations/done":
            self.send_error(404)
            return
        records = [record for record in read_records() if record["status"] != "Done"]
        write_records(records)
        self.send_json(records)

    def log_message(self, format, *args):
        print(f"{self.address_string()} - {format % args}")


def local_ip():
    connection = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        connection.connect(("8.8.8.8", 80))
        return connection.getsockname()[0]
    except OSError:
        return "localhost"
    finally:
        connection.close()


def public_url(port):
    configured = (
        os.environ.get("PIXCELLENS_PUBLIC_URL")
        or os.environ.get("PUBLIC_URL")
        or os.environ.get("APP_URL")
    )
    if configured:
        return configured.rstrip("/")
    return f"http://{local_ip()}:{port}"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    base_url = public_url(port)
    print(f"Picxellens office system: http://localhost:{port}")
    print(f"Customer QR address:    {base_url}/#register")
    print("Keep this window open while the office system is in use.")
    ThreadingHTTPServer(("0.0.0.0", port), OfficeHandler).serve_forever()