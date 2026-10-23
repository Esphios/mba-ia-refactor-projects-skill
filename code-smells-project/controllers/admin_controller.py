from flask import jsonify, request

from errors import APIError
from models.admin_model import AdminModel


admin = AdminModel()


def reset_database():
    admin.reset_database()
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200


def execute_query():
    payload = request.get_json(silent=True)
    sql = payload.get("sql", "") if isinstance(payload, dict) else ""
    if not isinstance(sql, str) or not sql.strip():
        raise APIError("Query não informada")
    rows, changed = admin.execute(sql)
    if changed:
        return jsonify({"mensagem": "Query executada", "sucesso": True}), 200
    return jsonify({"dados": rows, "sucesso": True}), 200
