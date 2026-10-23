"""Exercise every documented HTTP method/path against a running server."""

import json
import os
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen


BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:5051").rstrip("/")


def request(method, path, expected, *, token=None, payload=None):
    headers = {"Accept": "application/json"}
    body = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if payload is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(payload).encode("utf-8")
    call = Request(f"{BASE_URL}{path}", data=body, headers=headers, method=method)
    try:
        with urlopen(call, timeout=5) as response:
            status = response.status
            raw = response.read()
    except HTTPError as error:
        status = error.code
        raw = error.read()
    data = json.loads(raw) if raw else None
    if status != expected:
        raise AssertionError(f"{method} {path}: expected {expected}, observed {status}: {data}")
    print(json.dumps({"method": method, "path": path, "status": status}, ensure_ascii=False))
    return data


def login(email, password):
    return request(
        "POST", "/login", 200, payload={"email": email, "senha": password}
    )["token"]


def main():
    admin_password = os.environ["DEMO_ADMIN_PASSWORD"]
    customer_password = os.environ["DEMO_CUSTOMER_PASSWORD"]

    request("GET", "/", 200)
    request("GET", "/produtos", 200)
    request("GET", "/produtos/busca?q=Mouse&preco_min=80&preco_max=100", 200)
    request("GET", "/produtos/1", 200)

    admin_token = login("admin@loja.com", admin_password)
    customer_token = login("joao@email.com", customer_password)
    request("POST", "/admin/query", 403, token=customer_token, payload={"sql": "SELECT 1"})

    created_user = request(
        "POST",
        "/usuarios",
        201,
        payload={"nome": "Usuário HTTP", "email": "http@example.test", "senha": "http-user-password"},
    )
    new_user_id = created_user["dados"]["id"]
    new_user_token = login("http@example.test", "http-user-password")

    created_product = request(
        "POST",
        "/produtos",
        201,
        token=admin_token,
        payload={
            "nome": "Produto HTTP",
            "descricao": "Validação por processo real",
            "preco": 25,
            "estoque": 4,
            "categoria": "geral",
        },
    )
    product_id = created_product["dados"]["id"]
    request(
        "PUT",
        f"/produtos/{product_id}",
        200,
        token=admin_token,
        payload={
            "nome": "Produto HTTP Atualizado",
            "descricao": "Validação por processo real",
            "preco": 30,
            "estoque": 5,
            "categoria": "geral",
        },
    )
    request("DELETE", f"/produtos/{product_id}", 200, token=admin_token)

    users = request("GET", "/usuarios", 200, token=admin_token)
    if any("senha" in user or "password" in user for user in users["dados"]):
        raise AssertionError("GET /usuarios exposed a password field")
    detail = request("GET", f"/usuarios/{new_user_id}", 200, token=new_user_token)
    if "senha" in detail["dados"] or "password" in detail["dados"]:
        raise AssertionError("GET /usuarios/<id> exposed a password field")

    order = request(
        "POST",
        "/pedidos",
        201,
        token=customer_token,
        payload={"usuario_id": 2, "itens": [{"produto_id": 2, "quantidade": 2}]},
    )
    order_id = order["dados"]["pedido_id"]
    request("GET", "/pedidos", 200, token=admin_token)
    request("GET", "/pedidos/usuario/2", 200, token=customer_token)
    request(
        "PUT",
        f"/pedidos/{order_id}/status",
        200,
        token=admin_token,
        payload={"status": "aprovado"},
    )
    request("GET", "/relatorios/vendas", 200, token=admin_token)
    health = request("GET", "/health", 200)
    if {"secret_key", "db_path", "debug"} & set(health):
        raise AssertionError("GET /health exposed configuration")
    request(
        "POST", "/admin/query", 200, token=admin_token, payload={"sql": "SELECT COUNT(*) AS total FROM pedidos"}
    )
    request("POST", "/admin/reset-db", 200, token=admin_token)

    print(json.dumps({"result": "PASS", "contracts": 19}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(json.dumps({"result": "FAIL", "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        raise
