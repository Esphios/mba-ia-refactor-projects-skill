"""Own-process HTTP characterization. No existing database or server is used."""
import argparse
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import time


def worker(root, work):
    import shutil
    source = Path(work) / 'source'
    source.mkdir()
    for item in Path(root).iterdir():
        if item.is_file() and item.suffix == '.py':
            shutil.copy2(item, source / item.name)
        elif item.is_dir() and item.name in {'models', 'routes', 'controllers', 'services', 'utils'}:
            shutil.copytree(item, source / item.name, ignore=shutil.ignore_patterns('__pycache__'))
    sys.path.insert(0, str(source))
    os.chdir(work)
    import app as module
    from database import db
    from models.user import User
    from models.task import Task
    from models.category import Category
    from datetime import datetime
    from werkzeug.serving import make_server
    if hasattr(module, 'create_app'):
        app = module.create_app({'SECRET_KEY': secrets.token_hex(32), 'SQLALCHEMY_DATABASE_URI':
            'sqlite:///' + str(Path(work) / 'http.db'), 'LEGACY_MD5_CUTOFF': '2099-01-01T00:00:00'})
    else:
        app = module.app  # original snapshot's import side effect stays inside its disposable copy
    with app.app_context():
        db.create_all()
        for name, role in [('admin', 'admin'), ('owner', 'user'), ('other', 'user'), ('manager', 'manager')]:
            user = User(name=name, email=name + '@example.com', role=role)
            user.set_password('päss')
            user.created_at = datetime(2020, 1, 1)
            db.session.add(user)
        category = Category(name='Backend', color='#3498db', created_at=datetime(2020, 1, 1))
        db.session.add(category)
        db.session.flush()
        db.session.add(Task(title='Árvore 100%_ Unicode', description='Descrição', user_id=2,
            category_id=category.id, due_date=datetime(2000, 1, 1), tags='a,b',
            created_at=datetime(2020, 1, 1), updated_at=datetime(2020, 1, 1)))
        db.session.commit()
    server = make_server('127.0.0.1', 0, app)
    print('READY ' + str(server.server_port), flush=True)
    server.serve_forever()


def normalize(value):
    if isinstance(value, list):
        return [normalize(item) for item in value]
    if isinstance(value, dict):
        return {key: ('<dynamic>' if key in {'token', 'timestamp', 'generated_at', 'created_at', 'updated_at'} else normalize(item))
                for key, item in value.items() if key != 'password'}
    return value


def run(root, baseline=None):
    import requests
    with tempfile.TemporaryDirectory(prefix='task-skill-http-') as work:
        # Original is already a source-only disposable snapshot; never import user's original directly.
        command = [sys.executable, str(Path(__file__).resolve()), '--worker', '--root', str(root), '--work', work]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            encoding='utf-8', env={**os.environ, 'PYTHONUTF8': '1'},
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        try:
            import threading
            import queue
            lines = queue.Queue()
            server_lines = []
            def consume():
                for line in process.stdout:
                    lines.put(line)
            def consume_errors():
                for line in process.stderr:
                    server_lines.append(line)
            thread = threading.Thread(target=consume, daemon=True)
            error_thread = threading.Thread(target=consume_errors, daemon=True)
            thread.start()
            error_thread.start()
            deadline = time.monotonic() + 30
            port = None
            while time.monotonic() < deadline:
                try:
                    line = lines.get(timeout=.2)
                except queue.Empty:
                    if process.poll() is not None:
                        raise RuntimeError('Boot failed: ' + ''.join(server_lines))
                    continue
                if line.startswith('READY '):
                    port = int(line.split()[1])
                    break
            assert port, 'readiness timeout 30s'
            base = f'http://127.0.0.1:{port}'
            entries = []
            token = None
            def call(method, path, status=200, data=None):
                headers = {'Authorization': 'Bearer ' + token} if token else {}
                response = requests.request(method, base + path, json=data, headers=headers, timeout=10)
                assert response.status_code == status, (method, path, response.status_code, response.text)
                body = response.json()
                entries.append({'method': method, 'path': path, 'status': status, 'body': normalize(body)})
                return body
            call('GET', '/')
            call('GET', '/health')
            login = call('POST', '/login', data={'email': 'admin@example.com', 'password': 'päss'})
            token = login['token']
            call('GET', '/users')
            call('GET', '/users/2')
            created = call('POST', '/users', 201, {'name': 'Novo', 'email': 'new@example.com', 'password': '1234'})
            call('PUT', '/users/' + str(created['id']), data={'name': 'Atualizado'})
            call('GET', '/users/2/tasks')
            call('GET', '/tasks')
            call('GET', '/tasks/1')
            task = call('POST', '/tasks', 201, {'title': 'Outra tarefa', 'user_id': 2, 'category_id': 1,
                'priority': 2, 'tags': ['um', 'dois'], 'due_date': '2030-01-02'})
            call('PUT', '/tasks/' + str(task['id']), data={'status': 'done', 'due_date': None})
            call('GET', '/tasks/search?q=%25_&user_id=2')
            call('GET', '/tasks/stats')
            call('GET', '/reports/summary')
            call('GET', '/reports/user/2')
            call('GET', '/categories')
            category = call('POST', '/categories', 201, {'name': 'Nova'})
            call('PUT', '/categories/' + str(category['id']), data={'color': '#abcdef'})
            call('DELETE', '/categories/' + str(category['id']))
            call('DELETE', '/tasks/' + str(task['id']))
            call('DELETE', '/users/' + str(created['id']))
            assert len(entries) == 22
            if baseline:
                assert entries == baseline['contracts'], 'baseline contract difference outside approved normalization'
            security_checks = 0
            if 'def create_app' in (root / 'app.py').read_text(encoding='utf-8'):
                assert requests.get(base + '/tasks', timeout=10).status_code == 401
                assert requests.get(base + '/tasks', headers={'Authorization': 'Bearer fake-jwt-token-1'}, timeout=10).status_code == 401
                security_checks += 2
                def verify(method, path, expected, credential=token, data=None):
                    nonlocal security_checks
                    response = requests.request(method, base + path, json=data,
                        headers={'Authorization': 'Bearer ' + credential} if credential else {}, timeout=10)
                    assert response.status_code == expected, (method, path, expected, response.status_code, response.text)
                    security_checks += 1
                    return response.json()
                owner = verify('POST', '/login', 200, None, {'email': 'owner@example.com', 'password': 'päss'})['token']
                manager = verify('POST', '/login', 200, None, {'email': 'manager@example.com', 'password': 'päss'})['token']
                for path in ['/tasks/1', '/users/2', '/users/2/tasks', '/reports/user/2', '/categories']:
                    verify('GET', path, 200, owner)
                for path in ['/users/3', '/users/3/tasks', '/reports/user/3', '/reports/summary']:
                    verify('GET', path, 403, owner)
                verify('GET', '/reports/summary', 200, manager)
                verify('GET', '/users/3', 200, manager)
                mine = verify('POST', '/tasks', 201, owner, {'title': 'Owner success'})
                assert mine['user_id'] == 2
                verify('PUT', '/tasks/' + str(mine['id']), 200, owner, {'status': 'done'})
                verify('PUT', '/tasks/' + str(mine['id']), 403, owner, {'user_id': 3})
                verify('DELETE', '/tasks/' + str(mine['id']), 200, owner)
                verify('GET', '/tasks/' + str(mine['id']), 404, token)
                assigned = verify('POST', '/tasks', 201, manager, {'title': 'Assigned success', 'user_id': 3})
                verify('GET', '/tasks/' + str(assigned['id']), 403, owner)
                verify('DELETE', '/tasks/' + str(assigned['id']), 200, manager)
                managed = verify('POST', '/categories', 201, manager, {'name': 'Manager success'})
                verify('DELETE', '/categories/' + str(managed['id']), 200, manager)
                verify('POST', '/categories', 403, owner, {'name': 'Denied'})
                verify('PUT', '/users/2', 403, owner, {'role': 'admin'})
                verify('PUT', '/users/3', 403, manager, {'active': False})
                verify('POST', '/users', 403, None, {'name': 'Denied', 'email': 'denied@example.com', 'password': '1234', 'role': 'admin'})
                verify('PUT', '/users/4', 200, token, {'role': 'user'})
                verify('GET', '/reports/summary', 403, manager)
                verify('PUT', '/users/2', 200, token, {'active': False})
                verify('GET', '/tasks', 403, owner)
                verify('POST', '/login', 403, None, {'email': 'owner@example.com', 'password': 'päss'})
            result = {'contracts': entries, 'count': len(entries), 'pid': process.pid, 'port': port,
                'readiness_timeout_seconds': 30, 'command': [sys.executable, 'tests/run_http_matrix.py', '--worker'],
                'comparison': 'PASS' if baseline else ('approved contracts' if security_checks else 'original baseline'),
                'security_checks': security_checks, 'cleanup': None}
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)
            assert process.poll() is not None, 'own process still alive'
            error_thread.join(timeout=3)
            thread.join(timeout=3)
            stderr = ''.join(server_lines)
            process.stdout.close()
            process.stderr.close()
        result['cleanup'] = 'own child exited; temporary directory removed on return'
        result['server_log'] = stderr
        return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument('--worker', action='store_true')
    parser.add_argument('--work')
    parser.add_argument('--baseline')
    parser.add_argument('--output')
    args = parser.parse_args()
    if args.worker:
        worker(args.root, args.work)
    else:
        reference = json.loads(Path(args.baseline).read_text(encoding='utf-8-sig')) if args.baseline else None
        result = run(Path(args.root).resolve(), reference)
        output = json.dumps(result, ensure_ascii=False, indent=2)
        if args.output:
            Path(args.output).write_text(output, encoding='utf-8')
        print(json.dumps({key: result[key] for key in ['count', 'pid', 'port', 'comparison', 'cleanup']}, ensure_ascii=False))
