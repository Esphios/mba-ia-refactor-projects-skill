from functools import wraps

from flask import current_app, g, jsonify, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer


TOKEN_SALT = "access-token"


def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt=TOKEN_SALT)


def issue_token(user):
    return _serializer().dumps({"user_id": user["id"]})


def _unauthenticated():
    return jsonify({"erro": "Autenticação necessária", "sucesso": False}), 401


def _forbidden():
    return jsonify({"erro": "Acesso negado", "sucesso": False}), 403


def authenticate(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return _unauthenticated()
        token = header.removeprefix("Bearer ").strip()
        try:
            payload = _serializer().loads(
                token, max_age=current_app.config.get("TOKEN_MAX_AGE", 3600)
            )
        except (BadSignature, SignatureExpired):
            return _unauthenticated()

        from models.user_model import UserModel

        identity = UserModel().find_internal(payload.get("user_id"))
        if identity is None:
            return _unauthenticated()
        g.identity = identity
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    @authenticate
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.identity["tipo"] != "admin":
            return _forbidden()
        return view(*args, **kwargs)

    return wrapped


def owner_or_admin(parameter_name):
    def decorator(view):
        @authenticate
        @wraps(view)
        def wrapped(*args, **kwargs):
            owner_id = kwargs.get(parameter_name)
            if g.identity["tipo"] != "admin" and g.identity["id"] != owner_id:
                return _forbidden()
            return view(*args, **kwargs)

        return wrapped

    return decorator
