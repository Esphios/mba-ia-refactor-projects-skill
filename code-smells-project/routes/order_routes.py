from flask import Blueprint

from auth import admin_required, authenticate, owner_or_admin
from controllers import order_controller


blueprint = Blueprint("orders", __name__)

blueprint.post("/pedidos")(authenticate(order_controller.create_order))
blueprint.get("/pedidos")(admin_required(order_controller.list_orders))
blueprint.get("/pedidos/usuario/<int:usuario_id>")(
    owner_or_admin("usuario_id")(order_controller.list_user_orders)
)
blueprint.put("/pedidos/<int:pedido_id>/status")(
    admin_required(order_controller.update_order_status)
)
