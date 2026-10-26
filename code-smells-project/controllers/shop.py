from werkzeug.security import generate_password_hash

import auth
import serializers
import validators
from database import get_db, transaction
from domain import ORDER_STATUSES, sales_summary
from models.orders import Orders
from models.products import Products
from models.system import System
from models.users import Users
from services.checkout import checkout


class ShopController:
    def __init__(self, connection=get_db, unit_of_work=transaction):
        self.connection = connection
        self.unit_of_work = unit_of_work

    def products(self):
        return {'dados': Products(self.connection()).all(), 'sucesso': True}, 200

    def product(self, product_id):
        product = Products(self.connection()).get(product_id)
        if product is None:
            return {'erro': 'Produto não encontrado', 'sucesso': False}, 404
        return {'dados': product, 'sucesso': True}, 200

    def create_product(self, data):
        values = validators.product(data)
        with self.unit_of_work() as db:
            product_id = Products(db).create(values)
        return {'dados': {'id': product_id}, 'sucesso': True, 'mensagem': 'Produto criado'}, 201

    def update_product(self, product_id, data):
        with self.unit_of_work() as db:
            products = Products(db)
            if products.get(product_id) is None:
                return {'erro': 'Produto não encontrado'}, 404
            products.update(product_id, validators.product(data))
        return {'sucesso': True, 'mensagem': 'Produto atualizado'}, 200

    def delete_product(self, product_id):
        with self.unit_of_work() as db:
            products = Products(db)
            if products.get(product_id) is None:
                return {'erro': 'Produto não encontrado'}, 404
            products.delete(product_id)
        return {'sucesso': True, 'mensagem': 'Produto deletado'}, 200

    def search(self, term, category, minimum, maximum):
        results = Products(self.connection()).search(term, category,
            validators.search_bound(minimum), validators.search_bound(maximum))
        return {'dados': results, 'total': len(results), 'sucesso': True}, 200

    def users(self):
        return {'dados': Users(self.connection()).all(), 'sucesso': True}, 200

    def user(self, user_id):
        user = Users(self.connection()).get(user_id)
        if user is None:
            return {'erro': 'Usuário não encontrado'}, 404
        return {'dados': serializers.user(user), 'sucesso': True}, 200

    def create_user(self, data):
        name, email, password = validators.credentials(data, registering=True)
        password_hash = generate_password_hash(password)
        with self.unit_of_work() as db:
            user_id = Users(db).create(name, email, password_hash)
        return {'dados': {'id': user_id}, 'sucesso': True}, 201

    def login(self, data, token_ttl):
        _, email, password = validators.credentials(data)
        user = auth.login(email, password)
        if user is None:
            return {'erro': 'Email ou senha inválidos', 'sucesso': False}, 401
        return {'dados': serializers.user(user, login=True), 'sucesso': True,
            'mensagem': 'Login OK', 'token': auth.issue_token(user['id']), 'expires_in': token_ttl}, 200

    def create_order(self, data, identity, notify):
        user_id, items = validators.order(data)
        if identity['tipo'] != 'admin' and user_id != identity['id']:
            return {'erro': 'Acesso negado'}, 403
        with self.unit_of_work() as db:
            result = checkout(db, user_id, items)
        notify('Pedido criado; notificações locais simuladas (email/SMS/push).')
        return {'dados': result, 'sucesso': True, 'mensagem': 'Pedido criado com sucesso'}, 201

    def orders(self, user_id=None):
        return {'dados': Orders(self.connection()).list(user_id), 'sucesso': True}, 200

    def status(self, order_id, data, notify):
        status = validators.payload(data, allow_empty=True).get('status', '')
        if status not in ORDER_STATUSES:
            raise validators.InputError('Status inválido')
        with self.unit_of_work() as db:
            Orders(db).update_status(order_id, status)
        if status in ('aprovado', 'cancelado'):
            notify('Status atualizado; notificação local simulada.')
        return {'sucesso': True, 'mensagem': 'Status atualizado'}, 200

    def report(self):
        return {'dados': sales_summary(Orders(self.connection()).totals()), 'sucesso': True}, 200

    def health(self, debug):
        return {'status':'ok', 'database':'connected', 'counts':System(self.connection()).counts(),
            'versao':'1.0.0', 'ambiente':'producao', 'db_path':'loja.db', 'debug':debug}, 200

    def reset(self):
        with self.unit_of_work() as db:
            System(db).reset()
        return {'mensagem':'Banco de dados resetado', 'sucesso':True}, 200

    def query(self, data):
        query = validators.payload(data, allow_empty=True).get('sql', '')
        if not query:
            raise validators.InputError('Query não informada')
        validators.text(query)
        # Preserve arbitrary SQL, including transaction/DDL/PRAGMA capability.
        db = self.connection()
        try:
            result = System(db).query(query)
            if result is not None:
                return {'dados': result, 'sucesso': True}, 200
            db.commit()
        except BaseException:
            db.rollback()
            raise
        return {'mensagem':'Query executada', 'sucesso':True}, 200
