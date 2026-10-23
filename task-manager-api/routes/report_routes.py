from flask import Blueprint, jsonify
from controllers import report_controller as controller

report_bp = Blueprint("report", __name__)

@report_bp.route("/reports/summary", methods=["GET"])
def summary_report():
    return jsonify(controller.summary()), 200

@report_bp.route("/reports/user/<int:user_id>", methods=["GET"])
def user_report(user_id):
    return jsonify(controller.user_report(user_id)), 200
