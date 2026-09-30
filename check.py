#!/usr/bin/env python3
"""Check public entry points and keep a bounded public status history."""

import json
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).parent
PUBLIC = ROOT / "public"
RANGE_BYTES = 262144


def request(url, *, byte_range=False, save_to=None):
    output = str(save_to) if save_to else "/dev/null"
    command = [
        "curl", "--silent", "--show-error", "--location", "--connect-timeout", "7",
        "--max-time", "25", "--output", output,
        "--write-out", "%{http_code}\t%{size_download}\t%{time_total}",
    ]
    if byte_range:
        command += ["--range", f"0-{RANGE_BYTES - 1}"]
    result = subprocess.run(command + [url], capture_output=True, text=True, check=False)
    try:
        code, size, elapsed = result.stdout.strip().split("\t")
        code, size, elapsed = int(code), int(float(size)), round(float(elapsed), 2)
    except ValueError:
        code, size, elapsed = 0, 0, 0
    expected_code = 206 if byte_range else 200
    ok = result.returncode == 0 and code == expected_code
    if byte_range:
        ok = ok and size == RANGE_BYTES
    elif save_to:
        ok = ok and size >= 100
    detail = "正常" if ok else (f"HTTP {code}" if code else "连接失败")
    if code == expected_code and not ok:
        detail = "资源下载不完整或超时"
    return {"ok": ok, "http": code, "bytes": size, "seconds": elapsed, "detail": detail}


def check_services():
    with tempfile.TemporaryDirectory() as temp:
        temp = Path(temp)
        penpot_page = request("https://penpot.noxxxx.com/", save_to=temp / "penpot.html")
        penpot_js = request("https://penpot.noxxxx.com/js/libs.js", byte_range=True)
        sonar_page = request("https://sonar.noxxxx.com/", save_to=temp / "sonar.html")
        sonar_js = {"ok": False, "http": 0, "bytes": 0, "seconds": 0, "detail": "未找到主脚本"}
        if sonar_page["ok"]:
            html = (temp / "sonar.html").read_text(errors="replace")
            match = re.search(r'/js/main-[A-Za-z0-9_-]+\.js', html)
            if match:
                sonar_js = request("https://sonar.noxxxx.com" + match.group(), byte_range=True)
    return [
        {"id": "penpot", "name": "Penpot", "url": "https://penpot.noxxxx.com/",
         "up": penpot_page["ok"] and penpot_js["ok"],
         "checks": {"page": penpot_page, "javascript": penpot_js}},
        {"id": "sonar", "name": "SonarQube", "url": "https://sonar.noxxxx.com/",
         "up": sonar_page["ok"] and sonar_js["ok"],
         "checks": {"page": sonar_page, "javascript": sonar_js}},
    ]


def main():
    PUBLIC.mkdir(exist_ok=True)
    checked_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    services = check_services()
    status = {"checkedAt": checked_at, "services": services}
    (PUBLIC / "status.json").write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n")
    history_file = PUBLIC / "history.json"
    try:
        history = json.loads(history_file.read_text())
        if not isinstance(history, list):
            history = []
    except (FileNotFoundError, ValueError):
        history = []
    history.append({"time": checked_at, **{service["id"]: service["up"] for service in services}})
    history_file.write_text(json.dumps(history[-672:], ensure_ascii=False, indent=2) + "\n")
    for service in services:
        print(f"{service['name']}: {'UP' if service['up'] else 'DOWN'}")


if __name__ == "__main__":
    main()
