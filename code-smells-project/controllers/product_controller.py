from flask import jsonify, request

from errors import APIError, ConflictError, NotFoundError
from models.product_model import ProductModel
from services.product_service import validate_product


products = ProductModel()


def list_products():
    return jsonify({"dados": products.list_all(), "sucesso": True}), 200


def search_products():
    try:
        minimum = float(request.args["preco_min"]) if request.args.get("preco_min") else None
        maximum = float(request.args["preco_max"]) if request.args.get("preco_max") else None
    except ValueError as error:
        raise APIError("Faixa de preço inválida") from error
    result = products.search(
        request.args.get("q", ""), request.args.get("categoria"), minimum, maximum
    )
    return jsonify({"dados": result, "total": len(result), "sucesso": True}), 200


def get_product(product_id):
    product = products.find(product_id)
    if product is None:
        raise NotFoundError("Produto não encontrado")
    return jsonify({"dados": product, "sucesso": True}), 200


def create_product():
    values = validate_product(request.get_json(silent=True))
    product_id = products.create(values)
    return jsonify({
        "dados": {"id": product_id}, "sucesso": True, "mensagem": "Produto criado"
    }), 201


def update_product(product_id):
    if products.find(product_id) is None:
        raise NotFoundError("Produto não encontrado")
    products.update(product_id, validate_product(request.get_json(silent=True)))
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


def delete_product(product_id):
    if products.find(product_id) is None:
        raise NotFoundError("Produto não encontrado")
    if products.is_referenced(product_id):
        raise ConflictError("Produto possui histórico de pedidos")
    products.delete(product_id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200

