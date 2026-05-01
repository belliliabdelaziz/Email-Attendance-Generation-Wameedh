"""
Wameedh SC Bootcamp — Local Email Server
Run with:  python server.py
Then open: index.html in your browser (served from the same folder)

Endpoints:
  POST /test   — test SMTP connection
  POST /send   — send QR emails to all participants
"""

import json
import mimetypes
import os
import smtplib
import sys
import textwrap
import threading
from email.message import EmailMessage
from http.server import BaseHTTPRequestHandler, HTTPServer

# ── QR generation (optional — used when qr_out/ images don't exist yet) ───────
try:
    import qrcode
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False

PORT        = 5050
LOGO_CID    = "brand-logo"
DEFAULT_LOGO = "logoBootcamp.png"


# ─────────────────────────────────────────────────────────────────────────────
# Email helpers  (same logic as your original send_qr.py)
# ─────────────────────────────────────────────────────────────────────────────

def build_html(name: str, cfg: dict, logo_cid: str | None) -> str:
    primary    = cfg.get("brand_primary",    "#0B4F6C")
    accent     = cfg.get("brand_accent",     "#F5B700")
    background = cfg.get("brand_background", "#F6F7FB")
    text_color = cfg.get("brand_text",       "#1F2933")
    brand_name = cfg.get("brand_name",       "Wameedh SC Bootcamp")
    headline   = cfg.get("headline",         "Your QR code")
    greeting   = cfg.get("greeting",         "Good luck and see you soon.")

    logo_html = (
        f'<img src="cid:{logo_cid}" alt="{brand_name}" '
        f'style="height:52px;display:block;margin:0 auto 10px auto;">'
        if logo_cid else ""
    )

    return textwrap.dedent(f"""
    <html><body style="margin:0;padding:0;background:{background};">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{background};">
        <tr><td align="center" style="padding:28px 12px;">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
                 style="max-width:600px;background:#fff;border-radius:18px;overflow:hidden;
                        font-family:Trebuchet MS,Verdana,Arial,sans-serif;color:{text_color};
                        box-shadow:0 10px 28px rgba(16,24,40,.12);">
            <tr>
              <td style="background:{primary};padding:20px 28px;text-align:center;color:#fff;">
                {logo_html}
                <div style="font-size:14px;letter-spacing:2px;text-transform:uppercase;font-weight:600;">{brand_name}</div>
              </td>
            </tr>
            <tr>
              <td style="padding:28px;">
                <div style="font-size:22px;font-weight:700;color:{primary};margin-bottom:10px;">{headline}</div>
                <div style="font-size:16px;line-height:1.7;">Hi {name},</div>
                <div style="font-size:16px;line-height:1.7;margin-top:10px;">
                  Thanks for registering. Your QR code is attached — please show it at check-in.
                </div>
                <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
                       style="margin-top:18px;background:{background};border-left:4px solid {accent};border-radius:12px;">
                  <tr><td style="padding:12px 14px;font-size:14px;line-height:1.6;">
                    Check-in tip: keep this email handy and have your ID ready.
                  </td></tr>
                </table>
                <div style="font-size:16px;line-height:1.7;margin-top:16px;">{greeting}</div>
              </td>
            </tr>
            <tr>
              <td style="padding:0 28px 24px 28px;">
                <div style="height:1px;background:#E3E6EA;"></div>
                <div style="font-size:12px;color:#6B7280;margin-top:12px;">
                  If anything looks wrong, reply to this email and we will help.
                </div>
              </td>
            </tr>
          </table>
        </td></tr>
      </table>
    </body></html>
    """).strip()


def ensure_qr(name: str, qr_dir: str) -> str | None:
    """Return path to QR PNG, generating it if needed."""
    os.makedirs(qr_dir, exist_ok=True)
    path = os.path.join(qr_dir, name.replace(" ", "_") + ".png")
    if not os.path.exists(path):
        if not HAS_QRCODE:
            return None
        qrcode.make(name).save(path)
    return path


def smtp_connect(cfg: dict):
    host     = cfg.get("smtp_host", "smtp.gmail.com")
    port     = int(cfg.get("smtp_port", 465))
    use_ssl  = cfg.get("smtp_use_ssl", True)
    user     = cfg.get("smtp_user", "")
    password = cfg.get("smtp_pass", "")

    if use_ssl:
        server = smtplib.SMTP_SSL(host, port, timeout=10)
    else:
        server = smtplib.SMTP(host, port, timeout=10)
        server.starttls()

    server.login(user, password)
    return server


def send_one(cfg: dict, recipient: str, name: str, qr_dir: str) -> dict:
    try:
        sender  = cfg.get("sender", cfg.get("smtp_user", ""))
        subject = cfg.get("subject", "Your QR code")

        msg = EmailMessage()
        msg["From"]    = sender
        msg["To"]      = recipient
        msg["Subject"] = subject
        msg.set_content(f"Hi {name},\n\nYour QR code is attached. Please show it at check-in.\n")

        # Logo embed
        logo_path = cfg.get("logo_path", DEFAULT_LOGO)
        logo_cid  = LOGO_CID if (logo_path and os.path.exists(logo_path)) else None

        msg.add_alternative(build_html(name, cfg, logo_cid), subtype="html")

        if logo_cid:
            mime, _ = mimetypes.guess_type(logo_path)
            main, sub = (mime or "image/png").split("/", 1)
            with open(logo_path, "rb") as f:
                html_part = msg.get_payload()[-1]
                html_part.add_related(f.read(), maintype=main, subtype=sub,
                                      cid=logo_cid, filename=os.path.basename(logo_path))

        # QR attachment
        qr_path = ensure_qr(name, qr_dir)
        if qr_path:
            with open(qr_path, "rb") as f:
                msg.add_attachment(f.read(), maintype="image", subtype="png",
                                   filename=os.path.basename(qr_path))

        with smtp_connect(cfg) as server:
            server.send_message(msg)

        return {"ok": True, "name": name, "email": recipient}

    except smtplib.SMTPAuthenticationError:
        return {"ok": False, "name": name, "email": recipient,
                "error": "Auth failed — check email/password"}
    except smtplib.SMTPException as e:
        return {"ok": False, "name": name, "email": recipient, "error": str(e)}
    except OSError as e:
        return {"ok": False, "name": name, "email": recipient,
                "error": f"Network error: {e}"}
    except Exception as e:
        return {"ok": False, "name": name, "email": recipient,
                "error": f"{type(e).__name__}: {e}"}


# ─────────────────────────────────────────────────────────────────────────────
# HTTP server
# ─────────────────────────────────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        # Suppress default access log spam; print our own
        pass

    def send_json(self, data: dict, status: int = 200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        # CORS — allow the HTML file opened locally
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        # Preflight
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(length))
        except Exception:
            self.send_json({"ok": False, "error": "Invalid JSON"}, 400)
            return

        if self.path == "/test":
            self._handle_test(payload)
        elif self.path == "/send":
            self._handle_send(payload)
        else:
            self.send_json({"ok": False, "error": "Not found"}, 404)

    def _handle_test(self, payload: dict):
        cfg = payload.get("email", {})
        try:
            with smtp_connect(cfg):
                pass
            print(f"  [test] OK — {cfg.get('smtp_host')}:{cfg.get('smtp_port')}")
            self.send_json({"ok": True})
        except smtplib.SMTPAuthenticationError:
            self.send_json({"ok": False, "error": "Authentication failed — wrong email or app password"})
        except Exception as e:
            self.send_json({"ok": False, "error": str(e)})

    def _handle_send(self, payload: dict):
        cfg          = payload.get("email", {})
        participants = payload.get("participants", [])
        qr_dir       = payload.get("qr_dir", "qr_out")

        if not participants:
            self.send_json({"ok": False, "error": "No participants provided"})
            return

        results = []
        for p in participants:
            name  = p.get("name", "")
            email = p.get("email", "")
            if not email or "@" not in email:
                results.append({"ok": False, "name": name, "email": email,
                                 "error": "Invalid email"})
                continue
            r = send_one(cfg, email, name, qr_dir)
            results.append(r)
            status = "✓" if r["ok"] else "✗"
            print(f"  [send] {status} {name} <{email}>")

        ok_count  = sum(1 for r in results if r["ok"])
        err_count = len(results) - ok_count
        print(f"  [send] Done — {ok_count} sent, {err_count} failed")
        self.send_json({"ok": True, "results": results})


# ─────────────────────────────────────────────────────────────────────────────
# Also serve static files so you can open http://localhost:5050 directly
# ─────────────────────────────────────────────────────────────────────────────

class FullHandler(Handler):
    def do_GET(self):
        path = self.path.split("?")[0].lstrip("/") or "index.html"

        # Try several locations so the server works when static files live in
        # top-level, `web/` or `assets/` directories. The first existing file
        # wins.
        candidates = [path, os.path.join("web", path), os.path.join("assets", path)]

        for candidate in candidates:
            if os.path.exists(candidate):
                mime, _ = mimetypes.guess_type(candidate)
                with open(candidate, "rb") as f:
                    body = f.read()
                self.send_response(200)
                self.send_header("Content-Type", mime or "application/octet-stream")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(body)
                return

        # Not found in any candidate location
        self.send_response(404)
        self.end_headers()


def run():
    httpd = HTTPServer(("localhost", PORT), FullHandler)
    print("=" * 52)
    print("  Wameedh SC — Local Email Server")
    print(f"  Listening on http://localhost:{PORT}")
    print(f"  Open your browser at http://localhost:{PORT}")
    print("  Press Ctrl+C to stop")
    print("=" * 52)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")


if __name__ == "__main__":
    # Check dependencies
    missing = []
    try: import qrcode
    except ImportError: missing.append("qrcode")

    if missing:
        print(f"Optional packages not installed: {', '.join(missing)}")
        print("Install with:  pip install " + " ".join(missing))
        print("(Server will still run; QR codes must be pre-generated.)\n")

    run()
