from flask import Blueprint, request, jsonify
from controllers import category_controller as controller

category_bp = Blueprint("category", __name__)

@category_bp.route("/categories", methods=["GET"])
def get_categories():
    return jsonify(controller.listing()), 200

@category_bp.route("/categories", methods=["POST"])
def create_category():
    return jsonify(controller.write(request.get_json(silent=True))), 201

@category_bp.route("/categories/<int:cat_id>", methods=["PUT"])
def update_category(cat_id):
    return jsonify(controller.write(request.get_json(silent=True),cat_id)), 200

@category_bp.route("/categories/<int:cat_id>", methods=["DELETE"])
def delete_category(cat_id):
    return jsonify(controller.remove(cat_id)), 200
