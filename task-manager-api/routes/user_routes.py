from flask import Blueprint, request, jsonify
from controllers import user_controller as controller

user_bp = Blueprint("user", __name__)

@user_bp.route("/users", methods=["GET"])
def get_users():
    return jsonify(controller.listing()), 200

@user_bp.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    return jsonify(controller.detail(user_id)), 200

@user_bp.route("/users", methods=["POST"])
def create_user():
    return jsonify(controller.write(request.get_json(silent=True))), 201

@user_bp.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    return jsonify(controller.write(request.get_json(silent=True),user_id)), 200

@user_bp.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    return jsonify(controller.remove(user_id)), 200

@user_bp.route("/users/<int:user_id>/tasks", methods=["GET"])
def get_user_tasks(user_id):
    return jsonify(controller.tasks(user_id)), 200

@user_bp.route("/login", methods=["POST"])
def login():
    return jsonify(controller.login(request.get_json(silent=True))), 200
