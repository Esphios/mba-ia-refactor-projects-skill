def test_root_catalog_contract(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.get_json()["versao"] == "1.0.0"


def test_list_products_contract(client):
    response = client.get("/produtos")
    assert response.status_code == 200
    assert response.get_json()["sucesso"] is True
    assert len(response.get_json()["dados"]) == 10


def test_product_search_contract_and_invalid_number(client):
    response = client.get("/produtos/busca?q=Mouse&preco_min=80&preco_max=100")
    assert response.status_code == 200
    assert [item["nome"] for item in response.get_json()["dados"]] == ["Mouse Wireless"]

    invalid = client.get("/produtos/busca?preco_min=not-a-number")
    assert invalid.status_code == 400


def test_product_detail_contract(client):
    response = client.get("/produtos/1")
    assert response.status_code == 200
    assert response.get_json()["dados"]["nome"] == "Notebook Gamer"
    assert client.get("/produtos/9999").status_code == 404


def test_create_product_requires_admin_and_preserves_success_contract(client, admin_headers):
    denied = client.post("/produtos", json={"nome": "Livro", "preco": 50, "estoque": 2})
    assert denied.status_code == 401

    response = client.post(
        "/produtos",
        headers=admin_headers,
        json={"nome": "Livro", "descricao": "API", "preco": 50, "estoque": 2, "categoria": "livros"},
    )
    assert response.status_code == 201
    assert response.get_json()["sucesso"] is True


def test_update_product_requires_admin_and_uses_shared_validation(client, admin_headers):
    denied = client.put("/produtos/1", json={"nome": "Notebook", "preco": 1, "estoque": 1})
    assert denied.status_code == 401

    invalid = client.put(
        "/produtos/1",
        headers=admin_headers,
        json={"nome": "N", "preco": 1, "estoque": 1, "categoria": "invalid"},
    )
    assert invalid.status_code == 400

    updated = client.put(
        "/produtos/1",
        headers=admin_headers,
        json={"nome": "Notebook", "preco": 6000, "estoque": 9, "categoria": "informatica"},
    )
    assert updated.status_code == 200


def test_delete_product_blocks_historical_reference_but_deletes_unused(client, admin_headers):
    order = client.post(
        "/pedidos",
        headers=auth_headers_for(client, "joao@email.com", "customer-test-password"),
        json={"usuario_id": 2, "itens": [{"produto_id": 1, "quantidade": 1}]},
    )
    assert order.status_code == 201
    assert client.delete("/produtos/1", headers=admin_headers).status_code == 409
    assert client.delete("/produtos/10", headers=admin_headers).status_code == 200
    assert client.get("/produtos/10").status_code == 404


def test_list_users_is_admin_only_and_never_returns_password(client, admin_headers, customer_headers):
    assert client.get("/usuarios").status_code == 401
    assert client.get("/usuarios", headers=customer_headers).status_code == 403
    response = client.get("/usuarios", headers=admin_headers)
    assert response.status_code == 200
    assert all("senha" not in user and "password" not in user for user in response.get_json()["dados"])


def test_user_detail_allows_owner_or_admin(client, admin_headers, customer_headers):
    assert client.get("/usuarios/2", headers=customer_headers).status_code == 200
    assert client.get("/usuarios/3", headers=customer_headers).status_code == 403
    admin_view = client.get("/usuarios/3", headers=admin_headers)
    assert admin_view.status_code == 200
    assert "senha" not in admin_view.get_json()["dados"]


def test_create_user_is_public_and_duplicate_email_conflicts(client):
    payload = {"nome": "Nova", "email": "nova@example.test", "senha": "safe-password"}
    response = client.post("/usuarios", json=payload)
    assert response.status_code == 201
    assert client.post("/usuarios", json=payload).status_code == 409


def test_login_returns_expiring_token_and_rejects_injection(client):
    response = client.post(
        "/login", json={"email": "joao@email.com", "senha": "customer-test-password"}
    )
    assert response.status_code == 200
    assert isinstance(response.get_json().get("token"), str)
    assert response.get_json()["expires_in"] == 3600

    attack = client.post("/login", json={"email": "' OR 1=1 --", "senha": "wrong"})
    assert attack.status_code == 401


def test_create_order_requires_owner_and_preserves_total(client, customer_headers):
    assert client.post(
        "/pedidos", json={"usuario_id": 2, "itens": [{"produto_id": 2, "quantidade": 2}]}
    ).status_code == 401

    response = client.post(
        "/pedidos",
        headers=customer_headers,
        json={"usuario_id": 2, "itens": [{"produto_id": 2, "quantidade": 2}]},
    )
    assert response.status_code == 201
    assert response.get_json()["dados"]["total"] == 179.8


def test_list_all_orders_is_admin_only(client, admin_headers, customer_headers):
    assert client.get("/pedidos").status_code == 401
    assert client.get("/pedidos", headers=customer_headers).status_code == 403
    response = client.get("/pedidos", headers=admin_headers)
    assert response.status_code == 200
    assert response.get_json() == {"dados": [], "sucesso": True}


def test_list_user_orders_enforces_ownership(client, admin_headers, customer_headers):
    assert client.get("/pedidos/usuario/3", headers=customer_headers).status_code == 403
    assert client.get("/pedidos/usuario/2", headers=customer_headers).status_code == 200
    assert client.get("/pedidos/usuario/3", headers=admin_headers).status_code == 200


def test_update_order_status_requires_admin_and_reports_missing(client, admin_headers, customer_headers):
    assert client.put(
        "/pedidos/999/status", headers=customer_headers, json={"status": "aprovado"}
    ).status_code == 403
    assert client.put(
        "/pedidos/999/status", headers=admin_headers, json={"status": "aprovado"}
    ).status_code == 404


def test_sales_report_is_admin_only(client, admin_headers, customer_headers):
    assert client.get("/relatorios/vendas").status_code == 401
    assert client.get("/relatorios/vendas", headers=customer_headers).status_code == 403
    response = client.get("/relatorios/vendas", headers=admin_headers)
    assert response.status_code == 200
    assert response.get_json()["dados"]["total_pedidos"] == 0


def test_health_contract_is_public_and_sanitized(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"
    assert {"secret_key", "db_path", "debug"}.isdisjoint(response.get_json())


def test_reset_database_requires_admin_and_remains_functional(client, admin_headers):
    assert client.post("/admin/reset-db").status_code == 401
    response = client.post("/admin/reset-db", headers=admin_headers)
    assert response.status_code == 200
    assert response.get_json()["sucesso"] is True
    assert client.get("/produtos").get_json()["dados"] == []


def test_admin_query_retains_select_and_write_for_admin(client, admin_headers, customer_headers):
    assert client.post("/admin/query", json={"sql": "SELECT 1"}).status_code == 401
    assert client.post(
        "/admin/query", headers=customer_headers, json={"sql": "SELECT 1"}
    ).status_code == 403

    selected = client.post(
        "/admin/query", headers=admin_headers, json={"sql": "SELECT nome FROM produtos WHERE id = 1"}
    )
    assert selected.status_code == 200
    assert selected.get_json()["dados"] == [{"nome": "Notebook Gamer"}]

    written = client.post(
        "/admin/query",
        headers=admin_headers,
        json={"sql": "UPDATE produtos SET estoque = 7 WHERE id = 1"},
    )
    assert written.status_code == 200
    assert client.get("/produtos/1").get_json()["dados"]["estoque"] == 7


def auth_headers_for(client, email, password):
    response = client.post("/login", json={"email": email, "senha": password})
    assert response.status_code == 200
    token = response.get_json().get("token", "legacy-login-issued-no-token")
    return {"Authorization": f"Bearer {token}"}
