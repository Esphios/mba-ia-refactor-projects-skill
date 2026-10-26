"""Request-owned connections and explicit database administration."""
import sqlite3
from contextlib import contextmanager

import click
from flask import current_app, g
from werkzeug.security import generate_password_hash

SCHEMA = '''
CREATE TABLE IF NOT EXISTS produtos (
 id INTEGER PRIMARY KEY AUTOINCREMENT,nome TEXT,descricao TEXT,preco REAL,
 estoque INTEGER,categoria TEXT,ativo INTEGER DEFAULT 1,
 criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS usuarios (
 id INTEGER PRIMARY KEY AUTOINCREMENT,nome TEXT,email TEXT,senha TEXT,
 tipo TEXT DEFAULT 'cliente',criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS pedidos (
 id INTEGER PRIMARY KEY AUTOINCREMENT,usuario_id INTEGER,
 status TEXT DEFAULT 'pendente',total REAL,criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS itens_pedido (
 id INTEGER PRIMARY KEY AUTOINCREMENT,pedido_id INTEGER,produto_id INTEGER,
 quantidade INTEGER,preco_unitario REAL);
'''


def get_db():
    if 'db' not in g:
        connection = sqlite3.connect(current_app.config['DATABASE'], timeout=15)
        connection.row_factory = sqlite3.Row
        g.db = connection
    return g.db


def close_db(error=None):
    connection = g.pop('db', None)
    if connection is not None:
        connection.close()


@contextmanager
def transaction():
    connection = get_db()
    connection.execute('BEGIN IMMEDIATE')
    try:
        yield connection
        connection.commit()
    except BaseException:
        connection.rollback()
        raise


def init_app(app):
    app.teardown_appcontext(close_db)

    @app.cli.command('init-db')
    def init_db():
        """Create missing tables only; no seed or deletion."""
        get_db().executescript(SCHEMA)
        click.echo('Esquema inicializado; dados existentes preservados.')

    @app.cli.command('create-admin')
    @click.option('--email', prompt=True)
    @click.option('--nome', default='Admin')
    @click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True)
    def create_admin(email, nome, password):
        if not email or not password:
            raise click.ClickException('Email e senha são obrigatórios')
        with transaction() as db:
            db.execute('INSERT INTO usuarios(nome,email,senha,tipo) VALUES(?,?,?,?)',
                (nome, email, generate_password_hash(password), 'admin'))
        click.echo('Administrador criado.')

    @app.cli.command('seed-demo')
    @click.option('--disposable', is_flag=True, required=True,
        help='Confirma que este banco é descartável e vazio.')
    def seed_demo(disposable):
        with transaction() as db:
            if any(db.execute('SELECT COUNT(*) FROM ' + table).fetchone()[0]
                   for table in ('produtos', 'usuarios', 'pedidos', 'itens_pedido')):
                raise click.ClickException('Seed requer banco descartável vazio')
            db.executemany('INSERT INTO produtos(nome,descricao,preco,estoque,categoria) VALUES(?,?,?,?,?)', [
                ('Notebook Gamer','Notebook potente para jogos',5999.99,10,'informatica'),
                ('Mouse Wireless','Mouse sem fio ergonômico',89.90,50,'informatica'),
                ('Teclado Mecânico','Teclado mecânico RGB',299.90,30,'informatica'),
                ("Monitor 27''",'Monitor 27 polegadas 144hz',1899.90,15,'informatica'),
                ('Headset Gamer','Headset com microfone',199.90,25,'informatica'),
                ('Cadeira Gamer','Cadeira ergonômica',1299.90,8,'moveis'),
                ('Webcam HD','Webcam 1080p',249.90,20,'informatica'),
                ('Hub USB','Hub USB 3.0 7 portas',79.90,40,'informatica'),
                ('SSD 1TB','SSD NVMe 1TB',449.90,35,'informatica'),
                ('Camiseta Dev','Camiseta estampa código',59.90,100,'vestuario')])
        click.echo('Catálogo demonstrativo criado; nenhuma conta inserida.')
