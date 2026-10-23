from flask import current_app, jsonify, request

from auth import issue_token
from errors import APIError, ConflictError, NotFoundError
from models.user_model import PUBLIC_USER_FIELDS, UserModel


users = UserModel()


def list_users():
    return jsonify({"dados": users.list_all(), "sucesso": True}), 200


def get_user(user_id):
    user = users.find(user_id)
    if user is None:
        raise NotFoundError("Usuário não encontrado")
    return jsonify({"dados": user, "sucesso": True}), 200


def create_user():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise APIError("Dados inválidos")
    name = payload.get("nome")
    email = payload.get("email")
    password = payload.get("senha")
    if not all(isinstance(value, str) and value.strip() for value in (name, email, password)):
        raise APIError("Nome, email e senha são obrigatórios")
    if users.find_by_email(email):
        raise ConflictError("Email já cadastrado")
    user_id = users.create(name.strip(), email, password)
    return jsonify({"dados": {"id": user_id}, "sucesso": True}), 201


def login():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise APIError("Dados inválidos")
    email = payload.get("email", "")
    password = payload.get("senha", "")
    if not isinstance(email, str) or not isinstance(password, str) or not email or not password:
        raise APIError("Email e senha são obrigatórios")
    user = users.authenticate(email, password)
    if user is None:
        return jsonify({"erro": "Email ou senha inválidos", "sucesso": False}), 401
    public_user = {field: user[field] for field in PUBLIC_USER_FIELDS}
    return jsonify({
        "dados": public_user,
        "sucesso": True,
        "mensagem": "Login OK",
        "token": issue_token(user),
        "expires_in": current_app.config.get("TOKEN_MAX_AGE", 3600),
    }), 200
