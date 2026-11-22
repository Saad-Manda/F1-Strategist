"""Serve the prerequisites site (prerequisites/site) on http://127.0.0.1:8010 and open it in the browser.

The pages also open straight from disk. Use this if the sidebar's visited ticks or the hub's
"Continue" button do not carry across pages: some browsers give every file:// page its own
storage, and serving over http avoids that.

    python tools/serve.py [port]        (from the prerequisites/ folder)
"""

from __future__ import annotations

import functools
import http.server
import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "site"


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8010
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
    with http.server.ThreadingHTTPServer(("127.0.0.1", port), handler) as server:
        url = f"http://127.0.0.1:{port}/index.html"
        print(f"Serving {ROOT} at {url}  (Ctrl+C to stop)")
        webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
