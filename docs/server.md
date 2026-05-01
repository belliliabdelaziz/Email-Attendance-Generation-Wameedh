# server.py — API reference

This document describes the `server.py` endpoints and example payloads.

Overview
--------
The server listens on `http://localhost:5050` by default and exposes two POST endpoints:

- `POST /test` — verify SMTP credentials and connectivity.
- `POST /send` — send QR emails to a list of participants.

Content-Type
------------
All requests should set `Content-Type: application/json` and send a JSON body.

1) POST /test
---------------
Purpose: verify SMTP connection and credentials.

Example payload (`examples/test.json`):

```json
{
  "email": {
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 465,
    "smtp_use_ssl": true,
    "smtp_user": "youremail@example.com",
    "smtp_pass": "your_app_password",
    "sender": "youremail@example.com"
  }
}
```

Curl example:

```bash
curl -X POST http://localhost:5050/test \
  -H "Content-Type: application/json" \
  --data @examples/test.json
```

Success response:

```json
{ "ok": true }
```

Error response example:

```json
{ "ok": false, "error": "Authentication failed — wrong email or app password" }
```

2) POST /send
----------------
Purpose: send QR emails to many participants.

Example payload (`examples/send.json`):

```json
{
  "email": {
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 465,
    "smtp_use_ssl": true,
    "smtp_user": "youremail@example.com",
    "smtp_pass": "your_app_password",
    "sender": "youremail@example.com",
    "logo_path": "logoBootcamp.png"
  },
  "participants": [
    { "name": "Alice Example", "email": "alice@example.com" },
    { "name": "Bob Example", "email": "bob@example.com" }
  ],
  "qr_dir": "qr_out"
}
```

Curl example:

```bash
curl -X POST http://localhost:5050/send \
  -H "Content-Type: application/json" \
  --data @examples/send.json
```

Response format
---------------
The `/send` endpoint returns a JSON object with an array of per-recipient results under `results`. Each result object includes `ok`, `name`, `email` and optional `error` fields.

Notes
-----
- If `qrcode` is not installed, the server will still run but QR images must be pre-generated into `qr_out/` before calling `/send`.
- Use `launch_server_clean.py` to run the server from an isolated directory to avoid exposing unrelated project files.
