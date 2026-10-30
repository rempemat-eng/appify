#!/usr/bin/env python3
"""Serve the bundled Godot Web export on localhost and open it in a browser."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import argparse
import webbrowser


class Handler(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map, ".wasm": "application/wasm", ".pck": "application/octet-stream"}

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=0, help="Optional localhost port")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    directory = Path(__file__).resolve().parent / "web"
    if not (directory / "index.html").is_file():
        parser.error("The Web build is missing. Open project.godot in Godot and export the Web preset first.")
    with ThreadingHTTPServer(("127.0.0.1", args.port), partial(Handler, directory=str(directory))) as server:
        url = f"http://127.0.0.1:{server.server_port}/"
        print(f"MyGame · Roster Animation Studio\n{url}\nPress Ctrl+C to stop.", flush=True)
        if not args.no_browser:
            webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
