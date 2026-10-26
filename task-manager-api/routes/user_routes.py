from flask import Blueprint, jsonify, request
from controllers import user_controller as controller
from services.security import require

user_bp = Blueprint('users', __name__)


@user_bp.route('/users', methods=['GET'])
@require('admin', 'manager')
def get_users():
    payload, status = controller.get_users()
    return jsonify(payload), status


@user_bp.route('/users/<int:user_id>', methods=['GET'])
@require()
def get_user(user_id):
    payload, status = controller.get_user(user_id)
    return jsonify(payload), status


@user_bp.route('/users', methods=['POST'])
def create_user():
    payload, status = controller.create_user(request.get_json())
    return jsonify(payload), status


@user_bp.route('/users/<int:user_id>', methods=['PUT'])
@require()
def update_user(user_id):
    payload, status = controller.update_user(user_id, request.get_json())
    return jsonify(payload), status


@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
@require('admin')
def delete_user(user_id):
    payload, status = controller.delete_user(user_id)
    return jsonify(payload), status


@user_bp.route('/users/<int:user_id>/tasks', methods=['GET'])
@require()
def get_user_tasks(user_id):
    payload, status = controller.get_user_tasks(user_id)
    return jsonify(payload), status


@user_bp.route('/login', methods=['POST'])
def login():
    payload, status = controller.login(request.get_json())
    return jsonify(payload), status
