from flask import Blueprint, current_app, g, jsonify, request
from auth import require_identity
from controllers.shop import ShopController


def register_routes(app):
    routes = Blueprint('shop', __name__)
    controller = ShopController()

    def respond(result):
        body, status = result
        return jsonify(body), status

    @routes.get('/')
    def index():
        return jsonify({'mensagem':'Bem-vindo à API da Loja', 'versao':'1.0.0',
            'endpoints':{'produtos':'/produtos','usuarios':'/usuarios','pedidos':'/pedidos',
            'login':'/login','relatorios':'/relatorios/vendas','health':'/health'}})

    @routes.get('/produtos')
    def products():
        return respond(controller.products())

    @routes.get('/produtos/busca')
    def search():
        return respond(controller.search(request.args.get('q',''),request.args.get('categoria'),
            request.args.get('preco_min'),request.args.get('preco_max')))

    @routes.get('/produtos/<int:id>')
    def product(id):
        return respond(controller.product(id))

    @routes.post('/produtos')
    @require_identity(admin=True)
    def create_product():
        return respond(controller.create_product(request.get_json()))

    @routes.put('/produtos/<int:id>')
    @require_identity(admin=True)
    def update_product(id):
        return respond(controller.update_product(id,request.get_json()))

    @routes.delete('/produtos/<int:id>')
    @require_identity(admin=True)
    def delete_product(id):
        return respond(controller.delete_product(id))

    @routes.get('/usuarios')
    @require_identity(admin=True)
    def users():
        return respond(controller.users())

    @routes.get('/usuarios/<int:id>')
    @require_identity(owner_parameter='id')
    def user(id):
        return respond(controller.user(id))

    @routes.post('/usuarios')
    def create_user():
        return respond(controller.create_user(request.get_json()))

    @routes.post('/login')
    def login():
        return respond(controller.login(request.get_json(),current_app.config['TOKEN_TTL']))

    @routes.post('/pedidos')
    @require_identity()
    def create_order():
        return respond(controller.create_order(request.get_json(),g.identity,current_app.logger.info))

    @routes.get('/pedidos')
    @require_identity(admin=True)
    def orders():
        return respond(controller.orders())

    @routes.get('/pedidos/usuario/<int:usuario_id>')
    @require_identity(owner_parameter='usuario_id')
    def user_orders(usuario_id):
        return respond(controller.orders(usuario_id))

    @routes.put('/pedidos/<int:pedido_id>/status')
    @require_identity(admin=True)
    def status(pedido_id):
        return respond(controller.status(pedido_id,request.get_json(),current_app.logger.info))

    @routes.get('/relatorios/vendas')
    @require_identity(admin=True)
    def report():
        return respond(controller.report())

    @routes.get('/health')
    def health():
        return respond(controller.health(current_app.debug))

    @routes.post('/admin/reset-db')
    @require_identity(admin=True)
    def reset():
        return respond(controller.reset())

    @routes.post('/admin/query')
    @require_identity(admin=True)
    def query():
        return respond(controller.query(request.get_json()))

    app.register_blueprint(routes)
