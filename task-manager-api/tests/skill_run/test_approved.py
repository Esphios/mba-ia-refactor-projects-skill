"""Acceptance tests created from the approved T01–T13 audit, not prior tests."""
import importlib
import os
from pathlib import Path
import sys

import pytest

ROOT = Path(os.environ.get('SKILL_RUN_ROOT', Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(ROOT))
application = importlib.import_module('app')
from database import db
from models.user import User


@pytest.fixture
def app(tmp_path):
    if hasattr(application, 'create_app'):
        result = application.create_app({'TESTING': True, 'SECRET_KEY': 'test-only-generated-secret',
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///' + str(tmp_path / 'fixture.db'),
            'LEGACY_MD5_CUTOFF': '2099-01-01T00:00:00'})
    else:
        result = application.app
        result.config['TESTING'] = True
    with result.app_context():
        db.drop_all()
        db.create_all()
        for name, role in [('owner', 'user'), ('other', 'user'), ('manager', 'manager'), ('admin', 'admin')]:
            user = User(name=name, email=name + '@example.com', role=role)
            user.set_password('päss')
            db.session.add(user)
        db.session.commit()
    yield result
    with result.app_context():
        db.session.remove()
        db.engine.dispose()


def auth(client, email='owner'):
    response = client.post('/login', json={'email': email + '@example.com', 'password': 'päss'})
    assert response.status_code == 200
    return {'Authorization': 'Bearer ' + response.json['token']}


def test_deleted_account_token_cannot_follow_reused_user_id(app):
    client = app.test_client()
    admin = auth(client, 'admin')

    created_user = client.post('/users', json={
        'name': 'Temporary user', 'email': 'temporary-user@example.com', 'password': 'päss'
    })
    assert created_user.status_code == 201
    former_user_id = created_user.json['id']
    former_user = auth(client, 'temporary-user')
    assert client.delete(f'/users/{former_user_id}', headers=admin).status_code == 200
    replacement = client.post('/users', json={
        'name': 'Replacement', 'email': 'replacement@example.com', 'password': 'safe-password'
    })
    assert replacement.status_code == 201 and replacement.json['id'] == former_user_id
    assert client.get(f'/users/{former_user_id}', headers=former_user).status_code == 401
    assert client.put(f'/users/{former_user_id}', json={'password': 'attacker-password'}, headers=former_user).status_code == 401
    assert client.post('/login', json={
        'email': 'replacement@example.com', 'password': 'safe-password'
    }).status_code == 200
    assert client.post('/login', json={
        'email': 'replacement@example.com', 'password': 'attacker-password'
    }).status_code == 401

    created_admin = client.post('/users', json={
        'name': 'Temporary admin', 'email': 'temporary-admin@example.com',
        'password': 'päss', 'role': 'admin'
    }, headers=admin)
    assert created_admin.status_code == 201
    former_admin_id = created_admin.json['id']
    former_admin = auth(client, 'temporary-admin')
    assert client.delete(f'/users/{former_admin_id}', headers=admin).status_code == 200
    privileged_replacement = client.post('/users', json={
        'name': 'Replacement admin', 'email': 'replacement-admin@example.com',
        'password': 'replacement-password', 'role': 'admin'
    }, headers=admin)
    assert privileged_replacement.status_code == 201
    assert privileged_replacement.json['id'] == former_admin_id
    assert client.get('/users', headers=former_admin).status_code == 401


def test_factory_has_no_import_time_schema():
    assert hasattr(application, 'create_app')


def test_password_response_and_hash(app):
    client = app.test_client()
    response = client.post('/login', json={'email': 'owner@example.com', 'password': 'päss'})
    assert response.status_code == 200
    assert 'password' not in response.json['user']
    with app.app_context():
        assert User.query.first().password.startswith('scrypt:')


def test_authentication_and_ownership(app):
    client = app.test_client()
    assert client.get('/tasks').status_code == 401
    assert client.get('/tasks', headers={'Authorization': 'Bearer fake-jwt-token-1'}).status_code == 401
    assert client.get('/users/2', headers=auth(client)).status_code == 403


def test_validation_type_errors_are_400(app):
    client = app.test_client()
    headers = auth(client)
    assert client.post('/tasks', json={'title': 'valid', 'priority': True}, headers=headers).status_code == 400


def test_public_registration_cannot_escalate(app):
    client = app.test_client()
    response = client.post('/users', json={'name': 'bad', 'email': 'bad@example.com', 'password': '1234', 'role': 'admin'})
    assert response.status_code == 403


def seed_tasks(app):
    from models.task import Task
    from models.category import Category
    from datetime import datetime
    with app.app_context():
        category = Category(name='Backend')
        db.session.add(category)
        db.session.flush()
        for identifier, title in [(1, 'Árvore 100%_'), (2, 'Outro dono')]:
            db.session.add(Task(title=title, description='Unicode descrição', user_id=identifier,
                category_id=category.id, due_date=datetime(2000, 1, 1), tags='um,dois'))
        db.session.add(Task(title='Sem dono'))
        db.session.commit()


def test_exact_method_path_inventory(app):
    actual = {(method, rule.rule) for rule in app.url_map.iter_rules() for method in rule.methods
              if method not in ('HEAD', 'OPTIONS') and rule.endpoint != 'static'}
    expected = {('GET', '/'), ('GET', '/health'), ('POST', '/login'), ('GET', '/users'), ('POST', '/users'),
        ('GET', '/users/<int:user_id>'), ('PUT', '/users/<int:user_id>'), ('DELETE', '/users/<int:user_id>'),
        ('GET', '/users/<int:user_id>/tasks'), ('GET', '/tasks'), ('POST', '/tasks'),
        ('GET', '/tasks/<int:task_id>'), ('PUT', '/tasks/<int:task_id>'), ('DELETE', '/tasks/<int:task_id>'),
        ('GET', '/tasks/search'), ('GET', '/tasks/stats'), ('GET', '/reports/summary'),
        ('GET', '/reports/user/<int:user_id>'), ('GET', '/categories'), ('POST', '/categories'),
        ('PUT', '/categories/<int:cat_id>'), ('DELETE', '/categories/<int:cat_id>')}
    assert actual == expected


def test_anonymous_matrix_and_malformed_tokens(app):
    client = app.test_client()
    protected = [('GET', '/users'), ('GET', '/users/1'), ('PUT', '/users/1'), ('DELETE', '/users/1'),
        ('GET', '/users/1/tasks'), ('GET', '/tasks'), ('POST', '/tasks'), ('GET', '/tasks/1'),
        ('PUT', '/tasks/1'), ('DELETE', '/tasks/1'), ('GET', '/tasks/search'), ('GET', '/tasks/stats'),
        ('GET', '/reports/summary'), ('GET', '/reports/user/1'), ('GET', '/categories'),
        ('POST', '/categories'), ('PUT', '/categories/1'), ('DELETE', '/categories/1')]
    for method, path in protected:
        assert client.open(path, method=method, json={'title': 'abc'}).status_code == 401
    for token in ['fake-jwt-token-1', 'garbage', '', 'Bearer']:
        assert client.get('/tasks', headers={'Authorization': token}).status_code == 401
    assert client.get('/').status_code == client.get('/health').status_code == 200


def test_owner_manager_admin_success_and_denial(app):
    seed_tasks(app)
    client = app.test_client()
    owner, manager, admin = auth(client), auth(client, 'manager'), auth(client, 'admin')
    assert [task['id'] for task in client.get('/tasks', headers=owner).json] == [1]
    assert len(client.get('/tasks', headers=manager).json) == 3
    assert client.get('/tasks/stats', headers=owner).json['total'] == 1
    for path in ['/tasks/2', '/tasks/3', '/users/2', '/users/2/tasks', '/reports/user/2']:
        assert client.get(path, headers=owner).status_code == 403
        assert client.get(path, headers=manager).status_code == 200
    assert client.get('/reports/summary', headers=owner).status_code == 403
    assert client.get('/reports/summary', headers=manager).status_code == 200
    assert client.get('/users', headers=owner).status_code == 403
    assert client.get('/users', headers=manager).status_code == 200
    for actor in (owner, manager):
        identifier = 1 if actor is owner else 3
        assert client.put(f'/users/{identifier}', json={'role': 'admin'}, headers=actor).status_code == 403
        assert client.put(f'/users/{identifier}', json={'active': False}, headers=actor).status_code == 403
        assert client.put('/users/2', json={'name': 'takeover'}, headers=actor).status_code == 403
        assert client.delete('/users/2', headers=actor).status_code == 403
    assert client.put('/users/1', json={'name': 'new owner'}, headers=owner).status_code == 200
    assert client.put('/users/2', json={'role': 'manager'}, headers=admin).status_code == 200
    for path, data in [('/tasks/1', {'user_id': 2}), ('/tasks/1', {'user_id': None})]:
        assert client.put(path, json=data, headers=owner).status_code == 403
    assert client.put('/tasks/1', json={'status': 'done'}, headers=owner).status_code == 200
    assert client.put('/tasks/2', json={'user_id': 1}, headers=manager).status_code == 200
    assert client.get('/tasks/2', headers=owner).status_code == 200
    assert client.delete('/tasks/2', headers=owner).status_code == 200
    created = client.post('/tasks', json={'title': 'Própria'}, headers=owner)
    assert created.status_code == 201 and created.json['user_id'] == 1
    for identifier in (None, 2):
        assert client.post('/tasks', json={'title': 'Negada', 'user_id': identifier}, headers=owner).status_code == 403
    assert client.post('/tasks', json={'title': 'Sem dono', 'user_id': None}, headers=manager).status_code == 201
    for actor in (manager, admin):
        category = client.post('/categories', json={'name': 'Gerenciada'}, headers=actor)
        assert category.status_code == 201
        path = '/categories/' + str(category.json['id'])
        assert client.put(path, json={'color': 'opaque'}, headers=actor).status_code == 200
        assert client.delete(path, headers=actor).status_code == 200
    assert client.post('/categories', json={'name': 'negada'}, headers=owner).status_code == 403
    elevated = client.post('/users', json={'name': 'Novo admin', 'email': 'new@example.com', 'password': '1234', 'role': 'admin'}, headers=admin)
    assert elevated.status_code == 201 and elevated.json['role'] == 'admin'
    assert client.delete('/users/1', headers=admin).status_code == 200
    from models.task import Task
    with app.app_context():
        assert db.session.get(User, 1) is None
        assert not Task.query.filter_by(user_id=1).all()


def test_current_role_active_status_and_expiration(app, monkeypatch):
    client = app.test_client()
    admin = auth(client, 'admin')
    assert client.get('/reports/summary', headers=admin).status_code == 200
    with app.app_context():
        db.session.get(User, 4).role = 'user'
        db.session.commit()
    assert client.get('/reports/summary', headers=admin).status_code == 403
    owner = auth(client)
    tampered = {'Authorization': owner['Authorization'][:-5] + 'abcde'}
    assert client.get('/tasks', headers=tampered).status_code == 401
    from itsdangerous.timed import TimestampSigner
    real_time = TimestampSigner.get_timestamp
    monkeypatch.setattr(TimestampSigner, 'get_timestamp', lambda self: real_time(self) + 3601)
    assert client.get('/tasks', headers=owner).status_code == 401
    monkeypatch.undo()
    with app.app_context():
        db.session.get(User, 1).active = False
        db.session.commit()
    assert client.get('/tasks', headers=owner).status_code == 403
    assert client.post('/login', json={'email': 'owner@example.com', 'password': 'päss'}).status_code == 403
    assert client.post('/login', json={'email': 'owner@example.com', 'password': 'wrong'}).status_code == 401


def test_md5_migration_cutoff_unicode_and_no_fallback(app, monkeypatch):
    import hashlib
    from datetime import datetime
    client = app.test_client()
    legacy = hashlib.md5('päss'.encode()).hexdigest()
    with app.app_context():
        db.session.get(User, 1).password = legacy
        db.session.commit()
    app.config.update(LEGACY_MD5_CUTOFF='2030-01-01T00:00:00', CLOCK=lambda: datetime(2029, 1, 1))
    assert client.post('/login', json={'email': 'owner@example.com', 'password': 'wrong'}).status_code == 401
    with app.app_context():
        assert db.session.get(User, 1).password == legacy
    assert client.post('/login', json={'email': 'owner@example.com', 'password': 'päss'}).status_code == 200
    with app.app_context():
        modern = db.session.get(User, 1).password
        assert modern.startswith('scrypt:')
    import services.security as security
    with monkeypatch.context() as patch:
        patch.setattr(security.hashlib, 'md5', lambda *args, **kwargs: pytest.fail('modern fallback attempted'))
        assert client.post('/login', json={'email': 'owner@example.com', 'password': 'wrong'}).status_code == 401
    with app.app_context():
        db.session.get(User, 1).password = legacy
        db.session.commit()
    app.config['CLOCK'] = lambda: datetime(2030, 1, 1)
    assert client.post('/login', json={'email': 'owner@example.com', 'password': 'päss'}).status_code == 401
    app.config['LEGACY_MD5_CUTOFF'] = None
    assert client.post('/login', json={'email': 'owner@example.com', 'password': 'päss'}).status_code == 401
    with app.app_context():
        assert db.session.get(User, 1).password == legacy


def test_salt_and_all_user_serializers(app):
    client = app.test_client()
    admin = auth(client, 'admin')
    responses = [client.get('/users', headers=admin), client.get('/users/1', headers=admin),
        client.put('/users/1', json={'name': 'Atualizado'}, headers=admin),
        client.post('/users', json={'name': 'Novo', 'email': 'new@example.com', 'password': 'päss'}),
        client.post('/login', json={'email': 'owner@example.com', 'password': 'päss'})]
    for response in responses:
        assert response.status_code in (200, 201)
        assert 'password' not in response.get_data(as_text=True)
        assert 'scrypt:' not in response.get_data(as_text=True)
    with app.app_context():
        assert db.session.get(User, 1).password != db.session.get(User, 2).password


def test_type_null_empty_omitted_boundaries_and_contracts(app):
    client = app.test_client()
    owner, admin = auth(client), auth(client, 'admin')
    for data in [None, [], ['abc'], 1, 'abc']:
        for method, path in [('POST', '/tasks'), ('POST', '/users'), ('POST', '/login'), ('POST', '/categories'), ('PUT', '/users/1')]:
            response = client.open(path, method=method, data=__import__('json').dumps(data), content_type='application/json', headers=admin)
            assert response.status_code == 400, (method, path, data, response.json)
    assert client.post('/tasks', data='{', content_type='application/json', headers=owner).status_code == 400
    for data in [{'title': 123}, {'title': None}, {'title': 'aa'}, {'title': 'x' * 201},
        {'title': 'abc', 'priority': True}, {'title': 'abc', 'priority': '3'}, {'title': 'abc', 'priority': None},
        {'title': 'abc', 'priority': float('nan')}, {'title': 'abc', 'priority': float('inf')},
        {'title': 'abc', 'priority': 10**300}, {'title': 'abc', 'priority': 0}, {'title': 'abc', 'priority': 6},
        {'title': 'abc', 'tags': [1]}, {'title': 'abc', 'tags': False}, {'title': 'abc', 'due_date': []},
        {'title': 'abc', 'due_date': '01/01/2030'}, {'title': 'abc', 'category_id': True}]:
        assert client.post('/tasks', json=data, headers=owner).status_code == 400, data
    for query in ['priority=abc', 'user_id=abc']:
        assert client.get('/tasks/search?' + query, headers=owner).status_code == 400
    for title, priority in [('abc', 1), ('x' * 200, 5), ('   ', 1.5)]:
        response = client.post('/tasks', json={'title': title, 'priority': priority, 'description': None, 'due_date': '', 'tags': []}, headers=owner)
        assert response.status_code == 201
        task_id = response.json['id']
        assert response.json['title'] == title
        assert response.json['due_date'] is None and response.json['tags'] == []
        assert 'overdue' not in response.json
        updated = client.put(f'/tasks/{task_id}', json={'description': None, 'due_date': None, 'tags': []}, headers=owner)
        assert updated.status_code == 200 and updated.json['title'] == title
        assert client.put(f'/tasks/{task_id}', json={}, headers=owner).status_code == 400
        assert client.get(f'/tasks/{task_id}', headers=owner).json['overdue'] is False
        assert 'user_name' in client.get('/tasks', headers=owner).json[0]
        assert 'user_name' not in client.get(f'/tasks/{task_id}', headers=owner).json
    category = client.post('/categories', json={'name': 'Cor livre', 'color': 'opaque'}, headers=admin).json
    assert client.put('/categories/' + str(category['id']), json={}, headers=admin).status_code == 200
    assert client.put('/categories/' + str(category['id']), json=None, headers=admin).status_code in (400, 415)
    assert client.post('/users', json={'name': 'four', 'email': 'four@example.com', 'password': '1234'}).status_code == 201
    assert client.get('/missing').status_code == 404
    assert client.patch('/tasks', headers=owner).status_code == 405


def test_like_unicode_and_empty_stats(app):
    client = app.test_client()
    owner = auth(client)
    assert client.get('/tasks/stats', headers=owner).json == {'total': 0, 'pending': 0, 'in_progress': 0, 'done': 0,
        'cancelled': 0, 'overdue': 0, 'completion_rate': 0}
    seed_tasks(app)
    for query in ['%25_', 'Árvore', 'árvore', 'Unicode', '%25', '_']:
        # SQLite LIKE ASCII-insensitive behavior is preserved; Unicode case is not silently changed.
        result = client.get('/tasks/search?q=' + query, headers=owner)
        assert result.status_code == 200
    assert len(client.get('/tasks/search?q=Árvore', headers=owner).json) == 1
    assert client.get('/tasks/search?q=árvore', headers=owner).json == []
    assert len(client.get('/tasks/search?q=unicode', headers=owner).json) == 1
    assert client.get('/tasks/search?user_id=2', headers=owner).json == []


def test_utc_boundary_and_distinct_serializers(app):
    from datetime import datetime, timedelta
    from models.task import Task
    from utils.domain import overdue
    point = datetime(2030, 1, 1)
    for status in ('pending', 'in_progress', 'done', 'cancelled'):
        task = Task(title='Boundary', due_date=point, status=status)
        assert not overdue(task, point)
        assert overdue(task, point + timedelta(microseconds=1)) == (status in ('pending', 'in_progress'))
    seed_tasks(app)
    client = app.test_client()
    owner = auth(client)
    item = client.get('/users/1/tasks', headers=owner).json[0]
    assert set(item) == {'id', 'title', 'description', 'status', 'priority', 'created_at', 'due_date', 'overdue'}
    assert item['due_date'] == '2000-01-01 00:00:00'
    assert item['overdue'] is True


def test_query_growth_is_constant(app, record_property):
    from sqlalchemy import event
    from models.task import Task
    from models.category import Category
    seed_tasks(app)
    client = app.test_client()
    admin = auth(client, 'admin')
    paths = ['/tasks', '/users', '/categories', '/reports/summary']
    counts = {}
    with app.app_context():
        engine = db.engine
    def measure():
        output = {}
        for path in paths:
            selects = []
            def observe(connection, cursor, statement, parameters, context, many):
                if statement.lstrip().upper().startswith('SELECT'):
                    selects.append(statement)
            event.listen(engine, 'before_cursor_execute', observe)
            try:
                response = client.get(path, headers=admin)
                assert response.status_code == 200
                output[path] = len(selects)
            finally:
                event.remove(engine, 'before_cursor_execute', observe)
        return output
    counts['small'] = measure()
    with app.app_context():
        for index in range(20):
            user = User(name=f'User{index}', email=f'u{index}@example.com', password='not-for-login')
            category = Category(name=f'Category{index}')
            db.session.add_all([user, category])
            db.session.flush()
            db.session.add(Task(title=f'Task{index}', user_id=user.id, category_id=category.id))
        db.session.commit()
    counts['large'] = measure()
    assert counts['small'] == counts['large'], counts
    print('QUERY_GROWTH ' + __import__('json').dumps(counts))
    record_property('query_counts', counts)


def test_crud_failure_rolls_back_all_entities(app, monkeypatch):
    from sqlalchemy.exc import SQLAlchemyError
    from models.task import Task
    from models import store
    seed_tasks(app)
    client = app.test_client()
    admin = auth(client, 'admin')
    real_delete = db.session.delete
    def fail_user_delete(entity):
        if isinstance(entity, User):
            raise SQLAlchemyError('injected')
        real_delete(entity)
    monkeypatch.setattr(db.session, 'delete', fail_user_delete)
    assert client.delete('/users/1', headers=admin).status_code == 500
    with app.app_context():
        assert db.session.get(User, 1) is not None
        assert Task.query.filter_by(user_id=1).count() == 1
    monkeypatch.undo()
    def fail_commit():
        db.session.flush()
        raise SQLAlchemyError('injected after flush')
    monkeypatch.setattr(db.session, 'commit', fail_commit)
    assert client.post('/tasks', json={'title': 'Should roll back'}, headers=admin).status_code == 500
    assert client.put('/tasks/1', json={'title': 'Should roll back'}, headers=admin).status_code == 500
    with app.app_context():
        assert Task.query.count() == 3
        assert db.session.get(Task, 1).title == 'Árvore 100%_'


@pytest.mark.parametrize('stage', ['deleted', 'users', 'categories', 'tasks'])
def test_seed_intermediate_failure_is_atomic(app, stage):
    from seed import seed_data
    from models.task import Task
    from models.category import Category
    seed_tasks(app)
    app.config['ALLOW_DISPOSABLE_SEED'] = True
    def fail(point):
        if point == stage:
            raise RuntimeError('injected ' + stage)
    with pytest.raises(RuntimeError, match='injected'):
        seed_data(app, replace=True, checkpoint=fail)
    with app.app_context():
        assert User.query.count() == 4
        assert Task.query.count() == 3
        assert Category.query.count() == 1
        assert db.session.get(Task, 1).title == 'Árvore 100%_'


def test_seed_guards_success_and_no_automatic_reseed(app):
    from seed import seed_data
    from models.task import Task
    from models.category import Category
    with pytest.raises(ValueError, match='descartável'):
        seed_data(app, replace=True)
    app.config['ALLOW_DISPOSABLE_SEED'] = True
    with pytest.raises(ValueError, match='não vazio'):
        seed_data(app)
    seed_data(app, replace=True)
    with app.app_context():
        assert User.query.count() == 3 and Task.query.count() == 10 and Category.query.count() == 4
        assert db.session.get(User, 1).password.startswith('scrypt:')
    with pytest.raises(ValueError, match='não vazio'):
        seed_data(app)


def test_import_factory_init_and_config_have_no_data_side_effect(tmp_path):
    import subprocess
    import json
    database = tmp_path / 'never-created.db'
    script = "import app; a=app.create_app({'SECRET_KEY':'test','SQLALCHEMY_DATABASE_URI':" + repr('sqlite:///' + str(database)) + "}); assert not a.debug; print('IMPORT_NO_DATABASE')"
    result = subprocess.run([sys.executable, '-c', script], cwd=ROOT, text=True, capture_output=True, timeout=20)
    assert result.returncode == 0, result.stderr
    assert not database.exists()
    with pytest.raises(ValueError, match='SECRET_KEY'):
        application.create_app({'SECRET_KEY': None})
    instance = application.create_app({'SECRET_KEY': 'test', 'SQLALCHEMY_DATABASE_URI': 'sqlite:///' + str(database)})
    assert not database.exists()
    assert instance.test_cli_runner().invoke(args=['init-db']).exit_code == 0
    assert database.exists()
    assert instance.test_cli_runner().invoke(args=['init-db']).exit_code == 0
    with instance.app_context():
        db.session.remove()
        db.engine.dispose()


def test_legacy_database_opens_without_data_loss(tmp_path):
    import sqlite3
    import hashlib
    path = tmp_path / 'legacy.db'
    connection = sqlite3.connect(path)
    connection.executescript('''
        CREATE TABLE users (id INTEGER PRIMARY KEY, name VARCHAR(100) NOT NULL, email VARCHAR(150) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL, role VARCHAR(50), active BOOLEAN, created_at DATETIME);
        CREATE TABLE categories (id INTEGER PRIMARY KEY, name VARCHAR(100) NOT NULL, description VARCHAR(300), color VARCHAR(7), created_at DATETIME);
        CREATE TABLE tasks (id INTEGER PRIMARY KEY, title VARCHAR(200) NOT NULL, description TEXT, status VARCHAR(50), priority INTEGER,
            user_id INTEGER REFERENCES users(id), category_id INTEGER REFERENCES categories(id), created_at DATETIME, updated_at DATETIME,
            due_date DATETIME, tags VARCHAR(500));
    ''')
    connection.execute('INSERT INTO users VALUES (23,?,?,?,?,?,?)', ('Legado', 'old@example.com', hashlib.md5(b'1234').hexdigest(), 'admin', True, '2020-01-01 00:00:00'))
    connection.execute('INSERT INTO categories VALUES (17,?,?,?,?)', ('Legada', None, '#123456', '2020-01-01 00:00:00'))
    connection.execute('INSERT INTO tasks VALUES (99,?,?,?,?,?,?,?,?,?,?)', ('Tarefa legada', None, 'pending', 3, 23, 17,
        '2020-01-01 00:00:00', '2020-01-01 00:00:00', '2030-01-01 00:00:00', 'a,b'))
    connection.commit()
    before = list(connection.iterdump())
    instance = application.create_app({'SECRET_KEY': 'test', 'SQLALCHEMY_DATABASE_URI': 'sqlite:///' + str(path)})
    from services.security import issue_token
    with instance.app_context():
        token = issue_token(db.session.get(User, 23))
    response = instance.test_client().get('/tasks/99', headers={'Authorization': 'Bearer ' + token})
    assert response.status_code == 200
    assert response.json['user_id'] == 23 and response.json['category_id'] == 17
    assert response.json['tags'] == ['a', 'b'] and response.json['due_date'] == '2030-01-01 00:00:00'
    assert instance.test_cli_runner().invoke(args=['init-db']).exit_code == 0
    assert list(connection.iterdump()) == before
    connection.close()
    with instance.app_context():
        db.session.remove()
        db.engine.dispose()


def test_smtp_disabled_and_mockable():
    from services.notification_service import NotificationService
    assert NotificationService().send_email('example@example.com', 'subject', 'body') is False
    calls = []
    service = NotificationService(lambda *args: calls.append(args) or True)
    assert service.send_email('example@example.com', 'subject', 'body') is True
    assert len(calls) == 1


def test_inactive_legacy_password_is_not_upgraded(app):
    import hashlib
    legacy = hashlib.md5('päss'.encode()).hexdigest()
    with app.app_context():
        user = db.session.get(User, 1)
        user.password, user.active = legacy, False
        db.session.commit()
    client = app.test_client()
    assert client.post('/login', json={'email': 'owner@example.com', 'password': 'päss'}).status_code == 403
    with app.app_context():
        assert db.session.get(User, 1).password == legacy


def test_framework_error_shapes_and_ignored_create_fields(app):
    client = app.test_client()
    assert client.get('/missing').content_type.startswith('text/html')
    assert client.patch('/tasks').content_type.startswith('text/html')
    response = client.post('/users', json={'name': 'Ignored', 'email': 'ignored@example.com',
        'password': '1234', 'active': 'ignored-originally'})
    assert response.status_code == 201 and response.json['active'] is True


def test_legacy_null_status_is_overdue_in_stats_and_summary(app):
    from datetime import datetime
    from models.task import Task
    with app.app_context():
        task=Task(title='Legacy null', status='pending', due_date=datetime(2000,1,1), user_id=1)
        db.session.add(task); db.session.commit()
        db.session.execute(__import__('sqlalchemy').text('UPDATE tasks SET status=NULL WHERE id=:id'),{'id':task.id})
        db.session.commit(); task_id=task.id
    client=app.test_client(); headers=auth(client,'admin')
    assert client.get(f'/tasks/{task_id}',headers=headers).json['overdue'] is True
    assert client.get('/tasks/stats',headers=headers).json['overdue'] == 1
    summary=client.get('/reports/summary',headers=headers).json
    assert summary['overdue']['count'] == 1
    assert [row['id'] for row in summary['overdue']['tasks']] == [task_id]
