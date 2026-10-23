from flask import Blueprint

from auth import admin_required
from controllers import report_controller


blueprint = Blueprint("reports", __name__)
blueprint.get("/relatorios/vendas")(admin_required(report_controller.sales_report))

