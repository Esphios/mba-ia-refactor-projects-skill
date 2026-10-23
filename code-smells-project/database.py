import os
import sqlite3

import click
from flask import current_app, g


SCHEMA = """
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    descricao TEXT NOT NULL DEFAULT '',
    preco REAL NOT NULL,
    estoque INTEGER NOT NULL,
    categoria TEXT NOT NULL,
    ativo INTEGER NOT NULL DEFAULT 1,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT NOT NULL,
    senha TEXT NOT NULL,
    tipo TEXT NOT NULL DEFAULT 'cliente',
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_usuarios_email ON usuarios(lower(email));
CREATE TABLE IF NOT EXISTS pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'pendente',
    total REAL NOT NULL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);
CREATE TABLE IF NOT EXISTS itens_pedido (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id INTEGER NOT NULL,
    produto_id INTEGER NOT NULL,
    quantidade INTEGER NOT NULL,
    preco_unitario REAL NOT NULL,
    FOREIGN KEY (pedido_id) REFERENCES pedidos(id),
    FOREIGN KEY (produto_id) REFERENCES produtos(id)
);
"""


DEMO_PRODUCTS = [
    ("Notebook Gamer", "Notebook potente para jogos", 5999.99, 10, "informatica"),
    ("Mouse Wireless", "Mouse sem fio ergonômico", 89.90, 50, "informatica"),
    ("Teclado Mecânico", "Teclado mecânico RGB", 299.90, 30, "informatica"),
    ("Monitor 27''", "Monitor 27 polegadas 144hz", 1899.90, 15, "informatica"),
    ("Headset Gamer", "Headset com microfone", 199.90, 25, "informatica"),
    ("Cadeira Gamer", "Cadeira ergonômica", 1299.90, 8, "moveis"),
    ("Webcam HD", "Webcam 1080p", 249.90, 20, "informatica"),
    ("Hub USB", "Hub USB 3.0 7 portas", 79.90, 40, "informatica"),
    ("SSD 1TB", "SSD NVMe 1TB", 449.90, 35, "informatica"),
    ("Camiseta Dev", "Camiseta estampa código", 59.90, 100, "vestuario"),
]

DEMO_USERS = [
    ("Admin", "admin@loja.com", "DEMO_ADMIN_PASSWORD", "admin"),
    ("João Silva", "joao@email.com", "DEMO_CUSTOMER_PASSWORD", "cliente"),
    ("Maria Santos", "maria@email.com", "DEMO_SECOND_CUSTOMER_PASSWORD", "cliente"),
]


def get_db():
    if "db" not in g:
        connection = sqlite3.connect(current_app.config["DATABASE"])
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        g.db = connection
    return g.db


def close_db(_error=None):
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def init_schema():
    connection = get_db()
    connection.executescript(SCHEMA)
    connection.commit()


def seed_demo_data():
    connection = get_db()
    product_count = connection.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
    user_count = connection.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
    if product_count == 0:
        connection.executemany(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            DEMO_PRODUCTS,
        )
    if user_count == 0:
        users = []
        for name, email, password_variable, role in DEMO_USERS:
            password = os.environ.get(password_variable)
            if not password:
                raise RuntimeError(
                    f"External demo password is required in {password_variable}"
                )
            users.append((name, email, password, role))
        # Test/demo credentials start in the legacy form to exercise controlled
        # one-time upgrade during successful login. Production never seeds them.
        connection.executemany(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            users,
        )
    connection.commit()


@click.command("init-db")
def init_db_command():
    init_schema()
    click.echo("Database schema initialized.")


@click.command("seed-demo")
def seed_demo_command():
    init_schema()
    seed_demo_data()
    click.echo("Demo data seeded.")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(seed_demo_command)

    if app.config.get("AUTO_INIT_DB"):
        with app.app_context():
            init_schema()
            if app.config.get("SEED_DATA"):
                seed_demo_data()
