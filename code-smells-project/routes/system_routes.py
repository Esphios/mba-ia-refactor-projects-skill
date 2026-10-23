from flask import Blueprint

from controllers import system_controller


blueprint = Blueprint("system", __name__)
blueprint.get("/")(system_controller.index)
blueprint.get("/health")(system_controller.health)
