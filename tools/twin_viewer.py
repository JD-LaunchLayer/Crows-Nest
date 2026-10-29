#!/usr/bin/env python3
"""Watch the time-lapse twin in the normal 3D world and journal, read-only.

    python3 tools/twin_viewer.py            # then open http://127.0.0.1:8766
    python3 tools/twin_viewer.py --lan      # also viewable from your phone (prints a private link)

It reads the twin's save from disk on every refresh, so it follows the twin
while tools/timelapse.py runs in another window. It cannot pause, change or
save anything, and it never touches the real Crow on port 8765. The clock
shown is the twin's fast-forward clock, not the real time.
"""
import argparse
import contextlib
import importlib.util
import io
import json
import secrets
import shutil
import socket
import sys
import tempfile
from datetime import datetime
from http.server import ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
REPO = HERE if (HERE / 'crow.py').exists() else Path('~/Crows-Nest').expanduser()
sys.path.insert(0, str(REPO))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--twin', default='~/crow-twin')
    parser.add_argument('--port', type=int, default=8766)
    parser.add_argument('--lan', action='store_true')
    args = parser.parse_args()
    twin = Path(args.twin).expanduser().resolve()
    save = twin / 'crow-save.json'
    if not save.exists():
        sys.exit(f'No twin found at {twin}. Start one with tools/timelapse.py first.')
    # A throwaway folder holds the code; the twin's own files are only ever read.
    work = Path(tempfile.mkdtemp(prefix='crow-twin-view-'))
    shutil.copy2(REPO / 'crow.py', work / 'crow.py')
    spec = importlib.util.spec_from_file_location('crow_twin_view', work / 'crow.py')
    app = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):
        spec.loader.exec_module(app)
    app.ROOT = twin  # reading-journal excerpts come from the twin's archive

    def reload():
        try:
            data = json.loads(save.read_text())
        except (OSError, ValueError):
            return  # mid-write; keep the previous snapshot
        app.state.clear()
        app.state.update(data)
        meta = data.get('twin', {})
        virtual = datetime.fromisoformat(meta.get('virtual_now') or meta.get('started_virtual'))
        app.CLOCK_OVERRIDE = lambda: virtual
        app.runtime.update(status=f'Time-lapse twin, read-only view · twin clock {virtual:%a %d %b %Y %H:%M}',
                           model_usage={})

    static = {'/': 'index.html', '/world.js': 'world.js', '/life_view.js': 'life_view.js', '/journal.js': 'journal.js',
              '/mobile_controls.js': 'mobile_controls.js', '/sky.js': 'sky.js',
              '/vendor/astronomy.browser.min.js': 'vendor/astronomy.browser.min.js',
              '/vendor/three.module.js': 'vendor/three.module.js'}

    class Viewer(app.Handler):
        def do_GET(self):
            if self.path in static:
                kind = 'text/html; charset=utf-8' if self.path == '/' else 'application/javascript'
                return self.send(200, (REPO / static[self.path]).read_bytes(), kind)
            if self.path.startswith('/api/'):
                reload()
            return super().do_GET()

        def do_POST(self):
            return self.send(403, b'This is a read-only view of the twin.', 'text/plain')

    if args.lan:
        app.ACCESS_TOKEN = secrets.token_urlsafe(24)
    reload()
    server = ThreadingHTTPServer(('0.0.0.0' if args.lan else '127.0.0.1', args.port), Viewer)
    print(f'Twin viewer: http://127.0.0.1:{args.port}' + (f'/#token={app.ACCESS_TOKEN}' if args.lan else ''))
    if args.lan:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
                probe.connect(('192.0.2.1', 9))
                address = probe.getsockname()[0]
        except OSError:
            address = '<your-PC-IP>'
        print(f'Phone link (same Wi-Fi): http://{address}:{args.port}/#token={app.ACCESS_TOKEN}')
    print('Read-only. Ctrl+C closes the viewer; the twin keeps running.')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


if __name__ == '__main__':
    main()
