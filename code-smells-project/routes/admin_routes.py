from flask import Blueprint

from auth import admin_required
from controllers import admin_controller


blueprint = Blueprint("admin", __name__)
blueprint.post("/admin/reset-db")(admin_required(admin_controller.reset_database))
blueprint.post("/admin/query")(admin_required(admin_controller.execute_query))
