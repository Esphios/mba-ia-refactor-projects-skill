from flask import Blueprint, jsonify, request
from controllers import task_controller as controller
from services.security import require

task_bp = Blueprint('tasks', __name__)


@task_bp.route('/tasks', methods=['GET'])
@require()
def list_tasks():
    payload, status = controller.list_tasks()
    return jsonify(payload), status


@task_bp.route('/tasks/<int:task_id>', methods=['GET'])
@require()
def get_task(task_id):
    payload, status = controller.get_task(task_id)
    return jsonify(payload), status


@task_bp.route('/tasks', methods=['POST'])
@require()
def create_task():
    payload, status = controller.create_task(request.get_json())
    return jsonify(payload), status


@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
@require()
def update_task(task_id):
    payload, status = controller.update_task(task_id, request.get_json())
    return jsonify(payload), status


@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
@require()
def delete_task(task_id):
    payload, status = controller.delete_task(task_id)
    return jsonify(payload), status


@task_bp.route('/tasks/search', methods=['GET'])
@require()
def search_tasks():
    payload, status = controller.search_tasks(request.args)
    return jsonify(payload), status


@task_bp.route('/tasks/stats', methods=['GET'])
@require()
def task_stats():
    payload, status = controller.task_stats()
    return jsonify(payload), status
