from flask import Blueprint, jsonify, request
from controllers import report_controller as controller
from services.security import require

report_bp = Blueprint('reports', __name__)


@report_bp.route('/reports/summary', methods=['GET'])
@require('admin', 'manager')
def summary_report():
    payload, status = controller.summary_report()
    return jsonify(payload), status


@report_bp.route('/reports/user/<int:user_id>', methods=['GET'])
@require()
def user_report(user_id):
    payload, status = controller.user_report(user_id)
    return jsonify(payload), status


@report_bp.route('/categories', methods=['GET'])
@require()
def get_categories():
    payload, status = controller.get_categories()
    return jsonify(payload), status


@report_bp.route('/categories', methods=['POST'])
@require('admin', 'manager')
def create_category():
    payload, status = controller.create_category(request.get_json())
    return jsonify(payload), status


@report_bp.route('/categories/<int:cat_id>', methods=['PUT'])
@require('admin', 'manager')
def update_category(cat_id):
    payload, status = controller.update_category(cat_id, request.get_json())
    return jsonify(payload), status


@report_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
@require('admin', 'manager')
def delete_category(cat_id):
    payload, status = controller.delete_category(cat_id)
    return jsonify(payload), status
