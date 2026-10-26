"""Disposable fixtures; works against original and approved factory contracts."""
import importlib
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@pytest.fixture
def shop(tmp_path):
    database = importlib.import_module('database')
    module = importlib.import_module('app')
    path = tmp_path / 'shop.sqlite'
    if hasattr(module, 'create_app'):
        app = module.create_app({'TESTING': True, 'DATABASE': str(path),
                                 'SECRET_KEY': 'test-only-random-boundary-secret',
                                 'LEGACY_PASSWORD_CUTOFF': '2099-01-01T00:00:00+00:00'})
        result = app.test_cli_runner().invoke(args=['init-db'])
        assert result.exit_code == 0, result.output
    else:
        database.db_connection = None
        database.db_path = str(path)
        app = module.app
        app.config.update(TESTING=True)
        database.get_db()
    with sqlite3.connect(path) as db:
        for table in ('itens_pedido', 'pedidos', 'produtos', 'usuarios'):
            db.execute('DELETE FROM ' + table)
        db.executemany('INSERT INTO usuarios(id,nome,email,senha,tipo) VALUES(?,?,?,?,?)', [
            (1, 'Admin', 'admin@example.test', 'administrative-password', 'admin'),
            (2, 'João', 'joao@example.test', 'senhâ-東京', 'cliente'),
            (3, 'Maria', 'maria@example.test', 'another-password', 'cliente')])
        db.executemany('INSERT INTO produtos(id,nome,descricao,preco,estoque,categoria) VALUES(?,?,?,?,?,?)', [
            (1, 'Café 東京', 'Ação e precisão', 12.5, 10, 'livros'),
            (2, 'Mouse', '', 7.25, 20, 'informatica')])
    client = app.test_client()
    headers = {}
    for name, email, password in [('admin', 'admin@example.test', 'administrative-password'),
                                  ('owner', 'joao@example.test', 'senhâ-東京'),
                                  ('other', 'maria@example.test', 'another-password')]:
        response = client.post('/login', json={'email': email, 'senha': password})
        assert response.status_code == 200
        token = response.get_json().get('token')
        headers[name] = {'Authorization': 'Bearer ' + token} if token else {}
    yield app, client, path, headers
    if hasattr(database, 'db_connection') and database.db_connection is not None:
        database.db_connection.close()
        database.db_connection = None


def rows(path, sql, args=()):
    with sqlite3.connect(path) as db:
        return db.execute(sql, args).fetchall()
