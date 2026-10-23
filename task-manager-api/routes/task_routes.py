from flask import Blueprint, request, jsonify
from controllers import task_controller as controller

task_bp = Blueprint("task", __name__)

@task_bp.route("/tasks", methods=["GET"])
def get_tasks():
    return jsonify(controller.listing(request.args)), 200

@task_bp.route("/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id):
    return jsonify(controller.detail(task_id)), 200

@task_bp.route("/tasks", methods=["POST"])
def create_task():
    return jsonify(controller.write(request.get_json(silent=True))), 201

@task_bp.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    return jsonify(controller.write(request.get_json(silent=True),task_id)), 200

@task_bp.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    return jsonify(controller.remove(task_id)), 200

@task_bp.route("/tasks/search", methods=["GET"])
def search_tasks():
    return jsonify(controller.listing(request.args,True)), 200

@task_bp.route("/tasks/stats", methods=["GET"])
def task_stats():
    return jsonify(controller.stats()), 200
