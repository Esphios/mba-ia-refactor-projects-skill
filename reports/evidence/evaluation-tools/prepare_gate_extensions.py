"""Prepare trigger/resumption fixtures, without running any audited application."""
import hashlib, json, pathlib, shutil, sys

root = pathlib.Path(sys.argv[1])
repo = pathlib.Path(__file__).resolve().parents[3]
skill = repo / 'code-smells-project/.agents/skills/refactor-arch'
for name in ('negative_trigger', 'resumed_approval'):
    target = root / name
    target.mkdir()
    shutil.copytree(skill, target / '.agents/skills/refactor-arch')
(root / 'negative_trigger/README.md').write_text('Welcome to the catlog.\n')
(root / 'resumed_approval/server.py').write_text('''"""Catlog health service."""
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200 if self.path == '/health' else 404)
        self.end_headers()
        if self.path == '/health':
            self.wfile.write(b'{"ok": true}')
if __name__ == '__main__':
    HTTPServer(('127.0.0.1', int(os.environ['PORT'])), Handler).serve_forever()
''')
before = {}
for name in ('negative_trigger', 'resumed_approval'):
    target = root / name
    before[name] = {str(p.relative_to(target)):hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in target.rglob('*') if p.is_file()}
(root / 'extension-before.json').write_text(json.dumps(before, indent=2))
print(json.dumps(before, indent=2))
