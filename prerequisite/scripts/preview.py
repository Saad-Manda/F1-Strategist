"""Preview the learning site at root or /site/; independent of cwd."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from paths import ROOT, SITE


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--subdirectory', action='store_true')
    parser.add_argument('--readings', action='store_true', help='Render authoring sources in memory over the active v2 site')
    args = parser.parse_args()
    directory = ROOT if args.subdirectory else SITE
    prefix = '/site/' if args.subdirectory else '/'
    overlays = {}
    if args.readings:
        from build_readings import render_outputs
        outputs, overlays = render_outputs()
        overlays.update(outputs)
    class PreviewHandler(SimpleHTTPRequestHandler):
        def do_GET(self):
            from urllib.parse import urlsplit, unquote
            path = unquote(urlsplit(self.path).path)
            if path.startswith(prefix):
                route = path[len(prefix):] or 'index.html'
                if route in overlays:
                    payload = overlays[route].encode('utf-8')
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json; charset=utf-8' if route.endswith('.json') else 'text/html; charset=utf-8')
                    self.send_header('Content-Length',str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                    return
            super().do_GET()
    with ThreadingHTTPServer(('127.0.0.1', args.port), partial(PreviewHandler, directory=str(directory))) as server:
        print(f'Preview: http://127.0.0.1:{server.server_port}{prefix}', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
