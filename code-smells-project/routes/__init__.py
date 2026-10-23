from .admin_routes import blueprint as admin_blueprint
from .order_routes import blueprint as order_blueprint
from .product_routes import blueprint as product_blueprint
from .report_routes import blueprint as report_blueprint
from .system_routes import blueprint as system_blueprint
from .user_routes import blueprint as user_blueprint


ALL_BLUEPRINTS = (
    system_blueprint,
    product_blueprint,
    user_blueprint,
    order_blueprint,
    report_blueprint,
    admin_blueprint,
)
