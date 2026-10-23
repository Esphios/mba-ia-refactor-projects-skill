from flask import Blueprint

from auth import admin_required, owner_or_admin
from controllers import user_controller


blueprint = Blueprint("users", __name__)

blueprint.get("/usuarios")(admin_required(user_controller.list_users))
blueprint.get("/usuarios/<int:user_id>")(
    owner_or_admin("user_id")(user_controller.get_user)
)
blueprint.post("/usuarios")(user_controller.create_user)
blueprint.post("/login")(user_controller.login)
