import hmac
from datetime import datetime, timezone

from flask import current_app

from werkzeug.security import check_password_hash, generate_password_hash

from database import get_db


PUBLIC_USER_FIELDS = ("id", "nome", "email", "tipo", "criado_em")


def serialize_user(row):
    return {field: row[field] for field in PUBLIC_USER_FIELDS}


def _is_modern_hash(value):
    return value.startswith(("scrypt:", "pbkdf2:"))


class UserModel:
    def list_all(self):
        rows = get_db().execute("SELECT * FROM usuarios ORDER BY id").fetchall()
        return [serialize_user(row) for row in rows]

    def find_internal(self, user_id):
        if user_id is None:
            return None
        row = get_db().execute(
            "SELECT * FROM usuarios WHERE id = ?", (user_id,)
        ).fetchone()
        return dict(row) if row else None

    def find(self, user_id):
        row = self.find_internal(user_id)
        return {field: row[field] for field in PUBLIC_USER_FIELDS} if row else None

    def find_by_email(self, email):
        row = get_db().execute(
            "SELECT * FROM usuarios WHERE lower(email) = lower(?)", (email.strip(),)
        ).fetchone()
        return dict(row) if row else None

    def create(self, name, email, password, role="cliente"):
        cursor = get_db().execute(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            (name, email.strip().lower(), generate_password_hash(password, method="scrypt"), role),
        )
        get_db().commit()
        return cursor.lastrowid

    def authenticate(self, email, password):
        user = self.find_by_email(email)
        if user is None:
            return None
        stored = user["senha"]
        if _is_modern_hash(stored):
            valid = check_password_hash(stored, password)
        else:
            cutoff = datetime.fromisoformat(current_app.config['LEGACY_PASSWORD_CUTOFF'])
            if datetime.now(timezone.utc) >= cutoff:
                return None
            valid = hmac.compare_digest(stored.encode('utf-8'), password.encode('utf-8'))
            if valid:
                new_hash = generate_password_hash(password, method="scrypt")
                get_db().execute(
                    "UPDATE usuarios SET senha = ? WHERE id = ?", (new_hash, user["id"])
                )
                get_db().commit()
                user["senha"] = new_hash
        return user if valid else None

