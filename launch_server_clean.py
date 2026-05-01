#!/usr/bin/env python3
"""
launch_server_clean.py

Create a minimal isolated folder (server_isolated/) containing only the files
needed by `server.py` and run the server from that folder. This prevents the
HTTP server from exposing unrelated project files when you browse
http://localhost:5050.

The script now understands a `web/` directory (copies its files into the
isolated folder root) and copies the `assets/` directory as a whole so image
assets referenced from HTML still resolve.

Usage:
  python launch_server_clean.py        # recreate server_isolated/, run server
  python launch_server_clean.py --keep # do not remove existing server_isolated/
  python launch_server_clean.py --cleanup # remove server_isolated/ after server stops
"""

from pathlib import Path
import shutil
import subprocess
import sys
import argparse


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def main() -> None:
    root = Path(__file__).resolve().parent
    isolated = root / "server_isolated"

    parser = argparse.ArgumentParser(description="Run server.py from an isolated folder")
    parser.add_argument("--keep", action="store_true", help="Do not remove existing server_isolated/")
    parser.add_argument("--cleanup", action="store_true", help="Remove server_isolated/ after server stops")
    args = parser.parse_args()

    if isolated.exists():
        if args.keep:
            print("Using existing server_isolated/")
        else:
            print("Removing existing server_isolated/")
            shutil.rmtree(isolated)

    isolated.mkdir(parents=True, exist_ok=True)

    # Always copy server.py and flask_server.py
    for srv_name in ("server.py", "flask_server.py"):
        srv = root / srv_name
        if srv.exists():
            print(f"Copying {srv_name}")
            copy_file(srv, isolated / srv_name)

    # Copy top-level config and participant data if present
    for name in ("config.json", "participants.csv"):
        src = root / name
        if src.exists():
            print(f"Copying {name}")
            copy_file(src, isolated / name)

    # Copy assets/ directory (images and other static assets)
    assets_src = root / "assets"
    if assets_src.exists() and assets_src.is_dir():
        print("Copying assets/ directory")
        copy_tree(assets_src, isolated / "assets")

    # If a web/ directory exists, copy its files into the isolated root
    web_src = root / "web"
    if web_src.exists() and web_src.is_dir():
        print("Copying web/ files into isolated root")
        for item in web_src.iterdir():
            if item.is_file():
                copy_file(item, isolated / item.name)
            elif item.is_dir():
                copy_tree(item, isolated / item.name)
    else:
        # Fallback: copy common web files from repo root
        for name in ("index.html", "app.js", "style.css"):
            src = root / name
            if src.exists():
                print(f"Copying {name}")
                copy_file(src, isolated / name)

    # Copy qr_out directory (if present) so pre-generated QR images remain accessible
    qr_src = root / "qr_out"
    if qr_src.exists() and qr_src.is_dir():
        print("Copying qr_out/ directory")
        copy_tree(qr_src, isolated / "qr_out")

    print("Isolated folder ready:", isolated)
    for item in sorted(isolated.iterdir()):
        print(" -", item.name)

    print("\nStarting flask_server.py (camera + attendance API) on port 5000...")
    flask_proc = None
    flask_srv = isolated / "flask_server.py"
    if flask_srv.exists():
        flask_proc = subprocess.Popen(
            [sys.executable, "flask_server.py"],
            cwd=str(isolated)
        )
        print("Flask server PID:", flask_proc.pid)

    print("Starting server.py (email + static files) on port 5050. Press Ctrl+C to stop.")
    try:
        subprocess.run([sys.executable, "server.py"], cwd=str(isolated))
    except KeyboardInterrupt:
        print("\nServer interrupted by user")
    finally:
        if flask_proc:
            flask_proc.terminate()
            print("Flask server stopped.")

    if args.cleanup:
        try:
            shutil.rmtree(isolated)
            print("Removed isolated folder:", isolated)
        except Exception as e:
            print("Failed to remove isolated folder:", e)


if __name__ == "__main__":
    main()
