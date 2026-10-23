import importlib
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def application(tmp_path, monkeypatch):
    database_path = tmp_path / "loja-test.db"
    secret = "test-secret-key-with-at-least-32-bytes"
    monkeypatch.setenv("SECRET_KEY", secret)
    monkeypatch.setenv("DATABASE", str(database_path))
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DEMO_ADMIN_PASSWORD", "admin-test-password")
    monkeypatch.setenv("DEMO_CUSTOMER_PASSWORD", "customer-test-password")
    monkeypatch.setenv("DEMO_SECOND_CUSTOMER_PASSWORD", "second-customer-test-password")

    database = importlib.import_module("database")
    legacy_connection = getattr(database, "db_connection", None)
    if legacy_connection is not None:
        legacy_connection.close()
    database.db_connection = None
    database.db_path = str(database_path)

    app_module = importlib.import_module("app")
    if hasattr(app_module, "create_app"):
        flask_app = app_module.create_app({
            "TESTING": True,
            "DATABASE": str(database_path),
            "SECRET_KEY": secret,
            "SEED_DATA": True,
            "AUTO_INIT_DB": True,
            "LEGACY_PASSWORD_CUTOFF": "2099-01-01T00:00:00+00:00",
        })
    else:
        flask_app = app_module.app
        flask_app.config.update(
            TESTING=True,
            DATABASE=str(database_path),
            SECRET_KEY=secret,
            AUTO_INIT_DB=True,
        )

    with flask_app.app_context():
        database.get_db()

    yield flask_app

    connection = getattr(database, "db_connection", None)
    if connection is not None:
        connection.close()
        database.db_connection = None


@pytest.fixture
def client(application):
    return application.test_client()


@pytest.fixture
def auth_headers(client):
    def login(email, password):
        response = client.post("/login", json={"email": email, "senha": password})
        assert response.status_code == 200
        payload = response.get_json()
        token = payload.get("token", "legacy-login-issued-no-token")
        return {"Authorization": f"Bearer {token}"}

    return login


@pytest.fixture
def admin_headers(auth_headers):
    return auth_headers("admin@loja.com", "admin-test-password")


@pytest.fixture
def customer_headers(auth_headers):
    return auth_headers("joao@email.com", "customer-test-password")

