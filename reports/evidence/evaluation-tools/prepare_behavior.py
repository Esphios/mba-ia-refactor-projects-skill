"""Disposable fixtures and real boot measurements; run BEFORE audited read-only phases."""
import hashlib, json, os, pathlib, shutil, sqlite3, subprocess, sys, tempfile, time, urllib.request

REPO = pathlib.Path(__file__).resolve().parents[3]
ROOT = pathlib.Path(tempfile.mkdtemp(prefix='refactor-arch-eval-'))
SKILL = REPO / 'code-smells-project/.agents/skills/refactor-arch'

def manifest(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file()}

route = '''from http.server import BaseHTTPRequestHandler, HTTPServer
import json, os
from urllib.parse import urlparse, parse_qs
from {service} import find_items
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != '/items':
            self.send_response(404); self.end_headers(); return
        result = find_items(parse_qs(parsed.query).get('name', [''])[0])
        body = json.dumps(result).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers(); self.wfile.write(body)
if __name__ == '__main__':
    HTTPServer(('127.0.0.1', int(os.environ['PORT'])), Handler).serve_forever()
'''
store = '''import os, sqlite3
def {fn}(name):
    with sqlite3.connect('file:' + os.environ['APP_DB'] + '?mode=ro', uri=True) as conn:
        return [dict(id=row[0], name=row[1]) for row in conn.execute(
            'SELECT id, name FROM items WHERE name = ?', (name,))]
'''
boots = []
for name, entry, service, model in [('control', 'server.py', 'service', 'model'),
                                    ('variation', 'src/launch.py', 'catalog_ops', 'records')]:
    target = ROOT / name
    code = target / pathlib.Path(entry).parent
    code.mkdir(parents=True)
    shutil.copytree(SKILL, target / '.agents/skills/refactor-arch')
    (target / 'AGENTS.md').write_text('Python standard library only. Analyze source; runtime is external configuration. No dependency installation needed.\n')
    (code / pathlib.Path(entry).name).write_text(route.format(service=service))
    (code / (service + '.py')).write_text(f'from {model} import select_items\ndef find_items(name):\n    return select_items(name)\n')
    (code / (model + '.py')).write_text(store.format(fn='select_items'))
    (target / 'pyproject.toml').write_text('[project]\nname="fixture-catalog"\nversion="1.0.0"\nrequires-python=">=3.10"\ndependencies=[]\n')
    db = target / 'fixture.sqlite'
    with sqlite3.connect(db) as conn:
        conn.execute('CREATE TABLE items(id INTEGER PRIMARY KEY, name TEXT)')
        conn.execute('INSERT INTO items VALUES(1, ?)', ('pencil',))
    import socket
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0)); port = sock.getsockname()[1]
    env = dict(os.environ, APP_DB=str(db), PORT=str(port), PYTHONDONTWRITEBYTECODE='1')
    process = subprocess.Popen([sys.executable, str(target / entry)], cwd=target, env=env,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        for attempt in range(100):
            try:
                with urllib.request.urlopen(f'http://127.0.0.1:{port}/items?name=pencil') as response:
                    normal = {'status':response.status, 'body':json.loads(response.read())}
                break
            except OSError: time.sleep(.03)
        else: raise RuntimeError('real boot failed')
        with urllib.request.urlopen(f'http://127.0.0.1:{port}/items?name=%27%20OR%201%3D1--') as response:
            injection = {'status':response.status, 'body':json.loads(response.read())}
        boots.append({'fixture':name, 'entry':entry, 'normal':normal, 'injection':injection})
    finally:
        process.terminate(); process.communicate(timeout=5)

unknown = ROOT / 'unknown'; unknown.mkdir()
shutil.copytree(SKILL, unknown / '.agents/skills/refactor-arch')
(unknown / 'program.qzz').write_bytes(b'QZZ\x00\x01opaque vendor bundle\x02')

partial = ROOT / 'partial'; partial.mkdir()
shutil.copytree(SKILL, partial / '.agents/skills/refactor-arch')
(partial / 'server.py').write_text('''from http.server import BaseHTTPRequestHandler
import sqlite3
# caller identity comes from a trusted gateway, but gateway supplies no role
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/payroll':
            rows = sqlite3.connect('payroll.sqlite').execute('SELECT salary FROM employees').fetchall()
            self.send_response(200); self.end_headers(); self.wfile.write(str(rows).encode())
''')
(partial / 'schema.sql').write_text('CREATE TABLE employees(id INTEGER PRIMARY KEY, salary INTEGER);\nCREATE TABLE identities(id TEXT PRIMARY KEY);\n')

cycle = ROOT / 'cycles'; cycle.mkdir()
shutil.copytree(SKILL, cycle / '.agents/skills/refactor-arch')
(cycle / 'state.json').write_text('{"imports":false,"mapping":false,"encoding":false,"contract":false}\n')
(cycle / 'validate.py').write_text('''import json, sys
from pathlib import Path
state = json.loads(Path(__file__).with_name('state.json').read_text())
for key, value in state.items():
    if not value:
        print('FAIL ' + key); sys.exit(1)
print('PASS')
''')
result = {'fixture_root':str(ROOT), 'python':sys.version, 'skill_source_manifest':manifest(SKILL),
          'real_boot_preparation':boots,
          'boot_equivalent':boots[0]['normal']==boots[1]['normal'] and boots[0]['injection']==boots[1]['injection'],
          'before':{p.name:manifest(p) for p in ROOT.iterdir() if p.is_dir()}}
(ROOT / 'preparation.json').write_text(json.dumps(result, indent=2))
print(json.dumps({'fixture_root':str(ROOT), 'boot':boots, 'equivalent':result['boot_equivalent']}))
