from flask import Blueprint

from auth import admin_required
from controllers import product_controller


blueprint = Blueprint("products", __name__)

blueprint.get("/produtos")(product_controller.list_products)
blueprint.get("/produtos/busca")(product_controller.search_products)
blueprint.get("/produtos/<int:product_id>")(product_controller.get_product)
blueprint.post("/produtos")(admin_required(product_controller.create_product))
blueprint.put("/produtos/<int:product_id>")(
    admin_required(product_controller.update_product)
)
blueprint.delete("/produtos/<int:product_id>")(
    admin_required(product_controller.delete_product)
)
