from flask import jsonify

from models.system_model import SystemModel


def index():
    return jsonify({
        "mensagem": "Bem-vindo à API da Loja",
        "versao": "1.0.0",
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health",
        },
    }), 200


def health():
    return jsonify({
        "status": "ok",
        "database": "connected",
        "counts": SystemModel().counts(),
        "versao": "1.0.0",
        "ambiente": "producao",
    }), 200
