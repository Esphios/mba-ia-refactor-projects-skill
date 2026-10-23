from flask import g, jsonify, request

from errors import APIError
from models.order_model import OrderModel
from services.order_service import OrderService


orders = OrderModel()
order_service = OrderService()


def create_order():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise APIError("Dados inválidos")
    user_id = payload.get("usuario_id")
    if isinstance(user_id, bool) or not isinstance(user_id, int):
        raise APIError("Usuario ID é obrigatório")
    if g.identity["tipo"] != "admin" and g.identity["id"] != user_id:
        raise APIError("Acesso negado", 403, success=False)
    result = order_service.create(user_id, payload.get("itens", []))
    return jsonify({
        "dados": result, "sucesso": True, "mensagem": "Pedido criado com sucesso"
    }), 201


def list_orders():
    return jsonify({"dados": orders.list_orders(), "sucesso": True}), 200


def list_user_orders(usuario_id):
    return jsonify({"dados": orders.list_orders(usuario_id), "sucesso": True}), 200


def update_order_status(pedido_id):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise APIError("Dados inválidos")
    order_service.update_status(pedido_id, payload.get("status", ""))
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
