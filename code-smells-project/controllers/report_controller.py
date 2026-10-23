from flask import jsonify

from services.report_service import ReportService


def sales_report():
    return jsonify({"dados": ReportService().sales_report(), "sucesso": True}), 200

