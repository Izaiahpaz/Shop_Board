#!/usr/bin/env python3
"""
Shop Board - production whiteboard fed by CCC ONE EMS exports.

Run:   python shop_board.py "C:\\path\\to\\EMS export folder"
Open:  http://localhost:8080   (or http://<this-pc-name>:8080 from a TV / other PC)

Files:  shop_board.py (this launcher)   config.py (settings)    dbf.py (database reader)
        ems_parser.py (EMS -> board row) board.py (state, watching, delivery)
        webserver.py (web server)       index.html (the page)
Needs only Python 3.8+ (no extra packages). Keep all the files in one folder.
"""
import argparse
import json
import os
import sys
import threading
import time

import config
from board import Board
from webserver import serve


def main():
    ap = argparse.ArgumentParser(description="Production board fed by CCC ONE EMS exports")
    ap.add_argument("folder", nargs="?", default=config.DEFAULT_FOLDER,
                    help="folder CCC ONE exports EMS files into (default: DEFAULT_FOLDER in config.py)")
    ap.add_argument("--port", type=int, default=config.DEFAULT_PORT)
    ap.add_argument("--host", default=config.DEFAULT_HOST,
                    help="use 127.0.0.1 to keep the board private to this PC")
    ap.add_argument("--interval", type=float, default=config.DEFAULT_SCAN_SECONDS,
                    help="seconds between folder scans")
    ap.add_argument("--state", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                    "board_state.json"))
    ap.add_argument("--auto-delete-date-out", action="store_true",
                    help="also auto-deliver (and delete files) when an export has a vehicle-out date")
    ap.add_argument("--once", action="store_true",
                    help="scan once, print the rows, exit (for testing)")
    a = ap.parse_args()

    if not a.folder:
        sys.exit("No folder set. Either run:  python shop_board.py \"C:\\path\\to\\EMS folder\"\n"
                 "or set DEFAULT_FOLDER in config.py.")
    if not os.path.isdir(a.folder):
        sys.exit(f"Folder not found: {a.folder}")
    board = Board(os.path.abspath(a.folder), a.state, a.auto_delete_date_out)
    board.scan()
    if a.once:
        print(json.dumps(board.snapshot(), indent=2))
        return

    def watch():
        while True:
            time.sleep(a.interval)
            try:
                board.scan()
            except Exception as e:
                print("scan error:", e)

    threading.Thread(target=watch, daemon=True).start()
    print(f"Shop Board watching {board.folder}\nOpen http://localhost:{a.port}  (Ctrl+C to stop)")
    try:
        serve(board, a.host, a.port)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
