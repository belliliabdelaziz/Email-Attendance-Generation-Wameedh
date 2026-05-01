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
QR_CID      = "qr-code"
DEFAULT_LOGO = "assets/wameedh.png"
HOLYTECH_LOGO = "assets/holytech_sticker.png"


# ─────────────────────────────────────────────────────────────────────────────
# Email helpers  (same logic as your original send_qr.py)
# ─────────────────────────────────────────────────────────────────────────────

def build_html(name: str, cfg: dict, logo_cid: str | None, qr_cid: str | None) -> str:
    """
    IEEE-style formal email template for Wameedh SC x HolyTech.
    Layout mirrors the look of IEEE conference communications:
      - Dark navy header bar with logo + event title
      - Gold accent divider
      - Serif body text (Times New Roman) for the formal tone
      - QR code info block with dashed border
      - Gold left-border tip callout
      - Navy footer with fine print
    """
    brand_name = cfg.get("brand_name",    "Wameedh SC x HolyTech")
    accent     = cfg.get("brand_accent",  "#F5B700")
    greeting   = cfg.get("greeting",      "Good luck and see you soon.")

    # Color palette — primary blue with complements
    primary    = "#225c94"
    primary_dark = "#1a4470"
    primary_light = "#3a7fc0"
    primary_pale = "#e8f1f7"
    navy_lt    = "#5a8bc4"

    logo_block = (
        f'<img src="cid:{logo_cid}" alt="{brand_name}" '
        f'style="height:65px;display:block;object-fit:contain;" />'
        if logo_cid
        else f'<span style="font-family:Arial,sans-serif;font-size:24px;font-weight:700;'
             f'color:{primary};letter-spacing:1px;">W</span>'
    )

    qr_img_block = (
        f'<img src="cid:{qr_cid}" alt="Your QR Code" '
        f'style="width:80px;height:80px;border:2px dashed {primary};" />'
        if qr_cid
        else f'<table role="presentation" cellpadding="0" cellspacing="0" '
             f'style="border:2px dashed {primary};width:80px;height:80px;"> '
             f'<tr><td align="center" valign="middle"> '
             f'<span style="font-family:Arial,sans-serif;font-size:24px; '
             f'color:{primary};opacity:0.35;">&#9707;</span> '
             f'</td></tr></table>'
    )

    return textwrap.dedent(f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width,initial-scale=1">
      <style>
        body {{ margin:0; padding:0; background:#f4f4f4; font-family:'Times New Roman',Times,serif; }}
        .email-container {{ width:100%; background:#f4f4f4; }}
        .email-wrapper {{ max-width:600px; margin:0 auto; background:#ffffff; }}
      </style>
    </head>
    <body style="margin:0;padding:0;background:#f4f4f4;">

    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f4;">
    <tr><td align="center" style="padding:20px 10px;">

      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;background:#ffffff;">

        <!-- Top accent bar -->
        <tr><td style="background:{primary_dark};height:8px;font-size:0;line-height:0;">&nbsp;</td></tr>

        <!-- Header: primary bg, logo left, title right -->
        <tr>
          <td style="background:{primary};padding:24px 28px;">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td style="width:100px;vertical-align:middle;padding-right:16px;">
                  <div style="background:{primary_pale};border-radius:4px;padding:10px 12px;
                               display:inline-block;line-height:1;text-align:center;width:auto;">
                    {logo_block}
                  </div>
                </td>
                <td style="vertical-align:middle;">
                  <div style="font-family:Arial,Helvetica,sans-serif;font-size:16px;
                               font-weight:700;color:#ffffff;margin:0 0 4px 0;
                               letter-spacing:0.3px;">{brand_name}</div>
                  <div style="font-family:Arial,Helvetica,sans-serif;font-size:11px;
                               color:{navy_lt};letter-spacing:1px;
                               text-transform:uppercase;">Official Participant Communication</div>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- Gold + primary divider bar -->
        <tr>
          <td style="font-size:0;line-height:0;">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td style="width:40%;background:{accent};height:5px;font-size:0;">&nbsp;</td>
                <td style="background:{primary};height:5px;font-size:0;">&nbsp;</td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- Body -->
        <tr>
          <td style="background:#ffffff;padding:32px 32px 26px 32px;">

            <!-- Registration confirmed badge -->
            <div style="display:inline-block;border:1px solid {primary};
                         font-family:Arial,Helvetica,sans-serif;
                         font-size:10px;font-weight:700;color:{primary};
                         letter-spacing:1.2px;text-transform:uppercase;
                         padding:4px 12px;margin-bottom:24px;">
              Registration Confirmed
            </div>

            <!-- Salutation -->
            <p style="font-size:15px;color:#222222;margin:0 0 14px 0;line-height:1.7;">
              Dear <strong>{name}</strong>,
            </p>

            <!-- Intro paragraph -->
            <p style="font-size:14px;color:#333333;line-height:1.8;margin:0 0 16px 0;">
              We are pleased to confirm your registration for the
              <strong>{brand_name}</strong>.
              Your personal QR code has been generated and is shown below.
            </p>

            <!-- QR info block -->
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
                   style="border:1px solid #dde3ec;background:{primary_pale};margin:20px 0;">
              <tr>
                <td style="padding:20px 20px;width:110px;vertical-align:middle;text-align:center;">
                  {qr_img_block}
                </td>
                <td style="padding:20px 20px 20px 12px;vertical-align:middle;">
                  <div style="font-family:Arial,Helvetica,sans-serif;font-size:13px;
                               font-weight:700;color:{primary};margin-bottom:6px;">
                    Your QR Code — {name}
                  </div>
                  <div style="font-family:Arial,Helvetica,sans-serif;font-size:12px;
                               color:#555555;line-height:1.6;">
                    Present this QR code at the check-in desk upon arrival.
                    Show it directly from your device or print it before coming.
                  </div>
                </td>
              </tr>
            </table>

            <!-- Tip callout — gold left border -->
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
                   style="border-left:4px solid {accent};background:#fffdf0;margin:18px 0;">
              <tr>
                <td style="padding:12px 14px;font-family:Arial,Helvetica,sans-serif;
                            font-size:12px;color:#444444;line-height:1.6;">
                  <strong style="color:{primary};">Check-in tip:</strong>
                  Ensure your screen brightness is set to maximum when presenting
                  the QR code for scanning. A printed copy is equally acceptable.
                </td>
              </tr>
            </table>

            <!-- Second paragraph -->
            <p style="font-size:14px;color:#333333;line-height:1.8;margin:0 0 18px 0;">
              If you encounter any issues or have questions prior to the event,
              please reply to this email and our team will assist you promptly.
            </p>

            <!-- Closing -->
            <p style="font-size:14px;color:#333333;line-height:1.8;margin:0 0 6px 0;">
              {greeting}
            </p>
            <p style="font-size:14px;color:#333333;line-height:1.8;margin:0 0 4px 0;">
              With warm regards,
            </p>
            <div style="font-family:Arial,Helvetica,sans-serif;font-size:13px;
                         font-weight:700;color:{primary};margin-top:8px;">
              The {brand_name} Team
            </div>
            <div style="font-family:Arial,Helvetica,sans-serif;font-size:11px;
                         color:#777777;letter-spacing:0.3px;">
              Organizing Committee &middot; Wameedh SC x HolyTech
            </div>

          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="background:{primary};padding:18px 28px;">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
                   style="border-top:1px solid {primary_dark};padding-top:14px;">
              <tr>
                <td>
                  <p style="font-family:Arial,Helvetica,sans-serif;font-size:10px;
                              color:{navy_lt};margin:0;line-height:1.7;">
                    This is an automated message sent on behalf of the {brand_name}.<br>
                    Please do not reply directly — contact the organizing team for assistance.
                  </p>
                </td>
                <td align="right" style="vertical-align:top;">
                  <div style="font-family:Arial,Helvetica,sans-serif;font-size:9px;
                               color:{navy_lt};letter-spacing:1px;
                               text-transform:uppercase;text-align:right;line-height:1.7;">
                    Wameedh SC<br>x HolyTech
                  </div>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- Bottom accent bar -->
        <tr><td style="background:{accent};height:5px;font-size:0;line-height:0;">&nbsp;</td></tr>

      </table>
    </td></tr>
    </table>

    </body>
    </html>
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
        msg.set_content(f"Hi {name},\n\nYour QR code is embedded in the HTML version of this email.\n")

        # Logo embed
        logo_path = cfg.get("logo_path", DEFAULT_LOGO)
        logo_cid  = LOGO_CID if (logo_path and os.path.exists(logo_path)) else None

        # QR embed
        qr_path = ensure_qr(name, qr_dir)
        qr_cid  = QR_CID if qr_path else None

        msg.add_alternative(build_html(name, cfg, logo_cid, qr_cid), subtype="html")

        # Embed logo as related image
        if logo_cid:
            mime, _ = mimetypes.guess_type(logo_path)
            main, sub = (mime or "image/png").split("/", 1)
            with open(logo_path, "rb") as f:
                html_part = msg.get_payload()[-1]
                html_part.add_related(f.read(), maintype=main, subtype=sub,
                                      cid=logo_cid, filename=os.path.basename(logo_path))

        # Embed QR code as related image
        if qr_cid:
            with open(qr_path, "rb") as f:
                html_part = msg.get_payload()[-1]
                html_part.add_related(f.read(), maintype="image", subtype="png",
                                      cid=qr_cid, filename=os.path.basename(qr_path))

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