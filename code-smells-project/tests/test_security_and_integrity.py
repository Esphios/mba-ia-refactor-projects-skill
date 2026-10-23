import pytest


def test_legacy_password_fallback_has_a_cutoff(application, client):
    application.config['LEGACY_PASSWORD_CUTOFF'] = '2000-01-01T00:00:00+00:00'
    response = client.post('/login', json={
        'email': 'joao@email.com', 'senha': 'customer-test-password',
    })
    assert response.status_code == 401


def test_legacy_unicode_password_can_be_upgraded(application, client):
    import database
    with application.app_context():
        connection = database.get_db()
        connection.execute('UPDATE usuarios SET senha = ? WHERE id = 2', ('senha-com-acentuação',))
        connection.commit()
    response = client.post('/login', json={
        'email': 'joao@email.com', 'senha': 'senha-com-acentuação',
    })
    assert response.status_code == 200
    with application.app_context():
        stored = database.get_db().execute('SELECT senha FROM usuarios WHERE id = 2').fetchone()[0]
    assert stored.startswith('scrypt:')


def test_concurrent_cancellations_restore_stock_once(application, client, customer_headers, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    import database
    from models.order_model import OrderModel
    from services.order_service import OrderService
    from errors import ConflictError

    before = client.get('/produtos/2').get_json()['dados']['estoque']
    created = client.post('/pedidos', headers=customer_headers, json={
        'usuario_id': 2, 'itens': [{'produto_id': 2, 'quantidade': 2}],
    })
    order_id = created.get_json()['dados']['pedido_id']
    barrier = Barrier(2)
    original_find = OrderModel.find

    def overlapping_read(self, identifier):
        result = original_find(self, identifier)
        # Force both unlocked callers to hold the same stale snapshot. A caller
        # that owns a write transaction already serializes this boundary.
        if not database.get_db().in_transaction:
            barrier.wait(timeout=5)
        return result

    monkeypatch.setattr(OrderModel, 'find', overlapping_read)

    def cancel():
        with application.app_context():
            try:
                OrderService().update_status(order_id, 'cancelado')
                return 'cancelled'
            except ConflictError:
                return 'conflict'

    with ThreadPoolExecutor(max_workers=2) as workers:
        results = list(workers.map(lambda _: cancel(), range(2)))
    assert sorted(results) == ['cancelled', 'conflict']
    assert client.get('/produtos/2').get_json()['dados']['estoque'] == before


@pytest.mark.parametrize('price', [float('inf'), float('nan'), 10 ** 400])
def test_nonfinite_product_prices_are_rejected(client, admin_headers, price):
    response = client.post('/produtos', headers=admin_headers,
                           json={'nome': 'Preço inválido', 'preco': price, 'estoque': 3})
    assert response.status_code == 400


def test_overflowing_order_total_is_rejected_without_writes(application, client, admin_headers, customer_headers):
    import database
    updated = client.put('/produtos/2', headers=admin_headers,
                         json={'nome': 'Limite finito', 'preco': 1e308, 'estoque': 4})
    assert updated.status_code == 200
    with application.app_context():
        before = database.get_db().execute('SELECT COUNT(*) FROM pedidos').fetchone()[0]
    response = client.post('/pedidos', headers=customer_headers, json={
        'usuario_id': 2, 'itens': [{'produto_id': 2, 'quantidade': 2}],
    })
    assert response.status_code == 400
    assert client.get('/produtos/2').get_json()['dados']['estoque'] == 4
    with application.app_context():
        assert database.get_db().execute('SELECT COUNT(*) FROM pedidos').fetchone()[0] == before


def test_client_errors_keep_http_status(client, admin_headers):
    assert client.get('/missing').status_code == 404
    assert client.patch('/produtos').status_code == 405
    assert client.post('/login', json={'email': 123, 'senha': 'x'}).status_code == 400
    assert client.put('/pedidos/1/status', headers=admin_headers,
                      json={'status': []}).status_code == 400


def test_empty_sales_report_has_zero_status_counts(client, admin_headers):
    report = client.get('/relatorios/vendas', headers=admin_headers)
    assert report.status_code == 200
    data = report.get_json()['dados']
    assert data['pedidos_pendentes'] == 0
    assert data['pedidos_aprovados'] == 0
    assert data['pedidos_cancelados'] == 0


def test_existing_legacy_database_opens_without_data_loss(tmp_path, monkeypatch):
    import sqlite3

    monkeypatch.setenv("SECRET_KEY", "legacy-validation-secret-with-32-bytes")
    from app import create_app

    legacy_path = tmp_path / "legacy-loja.db"
    connection = sqlite3.connect(legacy_path)
    connection.executescript("""
        CREATE TABLE produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL,
            descricao TEXT, preco REAL NOT NULL, estoque INTEGER NOT NULL,
            categoria TEXT, ativo INTEGER DEFAULT 1,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL,
            email TEXT NOT NULL, senha TEXT NOT NULL, tipo TEXT DEFAULT 'cliente',
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pendente', total REAL NOT NULL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE itens_pedido (
            id INTEGER PRIMARY KEY AUTOINCREMENT, pedido_id INTEGER NOT NULL,
            produto_id INTEGER NOT NULL, quantidade INTEGER NOT NULL,
            preco_unitario REAL NOT NULL
        );
    """)
    connection.execute(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        ("Produto legado", "preservado", 12.5, 3, "geral"),
    )
    connection.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        ("Pessoa legada", "legacy@example.test", "legacy-password", "cliente"),
    )
    connection.commit()
    connection.close()

    legacy_app = create_app({
        "TESTING": True,
        "DATABASE": str(legacy_path),
        "SECRET_KEY": "legacy-validation-secret-with-32-bytes",
        "AUTO_INIT_DB": True,
        "SEED_DATA": False,
        "LEGACY_PASSWORD_CUTOFF": "2099-01-01T00:00:00+00:00",
    })
    client = legacy_app.test_client()

    product = client.get("/produtos/1")
    assert product.status_code == 200
    assert product.get_json()["dados"]["nome"] == "Produto legado"
    login = client.post(
        "/login", json={"email": "legacy@example.test", "senha": "legacy-password"}
    )
    assert login.status_code == 200
    with legacy_app.app_context():
        import database

        stored = database.get_db().execute(
            "SELECT senha FROM usuarios WHERE email = ?", ("legacy@example.test",)
        ).fetchone()[0]
    assert stored.startswith("scrypt:")


def test_order_rejects_nonpositive_quantity_without_changing_stock(application, client, customer_headers):
    before = client.get("/produtos/1").get_json()["dados"]["estoque"]
    response = client.post(
        "/pedidos",
        headers=customer_headers,
        json={"usuario_id": 2, "itens": [{"produto_id": 1, "quantidade": -1}]},
    )
    assert response.status_code == 400
    assert client.get("/produtos/1").get_json()["dados"]["estoque"] == before


def test_order_aggregates_duplicate_products_before_stock_check(client, customer_headers):
    response = client.post(
        "/pedidos",
        headers=customer_headers,
        json={
            "usuario_id": 2,
            "itens": [
                {"produto_id": 6, "quantidade": 5},
                {"produto_id": 6, "quantidade": 5},
            ],
        },
    )
    assert response.status_code == 400
    assert client.get("/produtos/6").get_json()["dados"]["estoque"] == 8


def test_order_rolls_back_if_item_insert_fails(application, client, customer_headers):
    import database

    with application.app_context():
        database.get_db().execute("""
            CREATE TRIGGER fail_second_item
            BEFORE INSERT ON itens_pedido
            WHEN NEW.produto_id = 2
            BEGIN
                SELECT RAISE(ABORT, 'induced item failure');
            END
        """)
        database.get_db().commit()
    before_one = client.get("/produtos/1").get_json()["dados"]["estoque"]
    before_two = client.get("/produtos/2").get_json()["dados"]["estoque"]

    response = client.post(
        "/pedidos",
        headers=customer_headers,
        json={
            "usuario_id": 2,
            "itens": [
                {"produto_id": 1, "quantidade": 1},
                {"produto_id": 2, "quantidade": 1},
            ],
        },
    )
    assert response.status_code == 500
    assert client.get("/produtos/1").get_json()["dados"]["estoque"] == before_one
    assert client.get("/produtos/2").get_json()["dados"]["estoque"] == before_two


def test_cancelling_order_restores_stock_once(client, admin_headers, customer_headers):
    before = client.get("/produtos/2").get_json()["dados"]["estoque"]
    created = client.post(
        "/pedidos",
        headers=customer_headers,
        json={"usuario_id": 2, "itens": [{"produto_id": 2, "quantidade": 3}]},
    )
    order_id = created.get_json()["dados"]["pedido_id"]
    assert client.get("/produtos/2").get_json()["dados"]["estoque"] == before - 3

    cancelled = client.put(
        f"/pedidos/{order_id}/status", headers=admin_headers, json={"status": "cancelado"}
    )
    assert cancelled.status_code == 200
    assert client.get("/produtos/2").get_json()["dados"]["estoque"] == before
    assert client.put(
        f"/pedidos/{order_id}/status", headers=admin_headers, json={"status": "cancelado"}
    ).status_code == 409


def test_demo_seed_requires_external_passwords(application, monkeypatch):
    import database

    with application.app_context():
        database.get_db().execute("DELETE FROM usuarios")
        database.get_db().commit()
        monkeypatch.delenv("DEMO_ADMIN_PASSWORD")
        monkeypatch.delenv("DEMO_CUSTOMER_PASSWORD")
        monkeypatch.delenv("DEMO_SECOND_CUSTOMER_PASSWORD")
        with pytest.raises(RuntimeError, match="demo password"):
            database.seed_demo_data()


def test_passwords_are_hashed_and_legacy_login_upgrades_storage(application, client):
    import database

    response = client.post(
        "/login", json={"email": "joao@email.com", "senha": "customer-test-password"}
    )
    assert response.status_code == 200
    with application.app_context():
        stored = database.get_db().execute(
            "SELECT senha FROM usuarios WHERE email = ?", ("joao@email.com",)
        ).fetchone()[0]
    assert stored != "customer-test-password"
    assert stored.startswith("scrypt:")


def test_token_tampering_and_expiry_are_rejected(client, customer_headers):
    import time

    from itsdangerous import URLSafeTimedSerializer
    from itsdangerous.timed import TimestampSigner

    token = customer_headers["Authorization"].removeprefix("Bearer ")
    tampered = token[:-1] + ("a" if token[-1] != "a" else "b")
    assert client.get("/usuarios/2", headers={"Authorization": f"Bearer {tampered}"}).status_code == 401

    class BackdatedSigner(TimestampSigner):
        def get_timestamp(self):
            return int(time.time()) - 7200

    signer = URLSafeTimedSerializer(
        "test-secret-key-with-at-least-32-bytes",
        salt="access-token",
        signer=BackdatedSigner,
    )
    expired = signer.dumps({"user_id": 2})
    assert client.get(
        "/usuarios/2", headers={"Authorization": f"Bearer {expired}"}
    ).status_code == 401


def test_order_listing_uses_bounded_select_count(application, client, admin_headers, customer_headers):
    for _ in range(3):
        response = client.post(
            "/pedidos",
            headers=customer_headers,
            json={"usuario_id": 2, "itens": [{"produto_id": 2, "quantidade": 1}]},
        )
        assert response.status_code == 201

    import database

    statements = []
    with application.app_context():
        connection = database.get_db()
        connection.set_trace_callback(statements.append)
        response = client.get("/pedidos", headers=admin_headers)
        connection.set_trace_callback(None)

    assert response.status_code == 200
    selects = [statement for statement in statements if statement.lstrip().upper().startswith("SELECT")]
    # Authentication adds one constant identity lookup; order hydration must stay
    # bounded at two additional SELECTs regardless of order/item count.
    assert len(selects) <= 3


@pytest.mark.parametrize("threshold,expected", [
    (1000, 0),
    (1001, 20.02),
    (5000, 100),
    (5001, 250.05),
    (10000, 500),
    (10001, 1000.1),
])
def test_discount_boundaries_preserve_legacy_policy(
    threshold, expected, application, client, admin_headers
):
    import database

    with application.app_context():
        database.get_db().execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
            (2, "aprovado", threshold),
        )
        database.get_db().commit()
    response = client.get("/relatorios/vendas", headers=admin_headers)
    assert response.status_code == 200
    assert response.get_json()["dados"]["desconto_aplicavel"] == pytest.approx(expected)
