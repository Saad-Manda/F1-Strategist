"""Preview the learning site at root or /site/; independent of cwd."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from paths import ROOT, SITE


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--subdirectory', action='store_true')
    args = parser.parse_args()
    directory = ROOT if args.subdirectory else SITE
    prefix = '/site/' if args.subdirectory else '/'
    with ThreadingHTTPServer(('127.0.0.1', args.port), partial(SimpleHTTPRequestHandler, directory=str(directory))) as server:
        print(f'Preview: http://127.0.0.1:{server.server_port}{prefix}', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
