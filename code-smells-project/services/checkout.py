import math
from collections import defaultdict

from models.orders import Orders
from models.products import Products
from models.users import Users
from validators import InputError


def checkout(db, user_id, items):
    """Caller owns BEGIN IMMEDIATE across every read, decision and write."""
    if Users(db).get(user_id) is None:
        raise InputError('Usuário não encontrado', business=True)
    demand = defaultdict(int)
    for item in items:
        demand[item['produto_id']] += item['quantidade']
    products = Products(db)
    loaded = products.by_ids(tuple(demand))
    total = 0
    for item in items:
        product = loaded.get(item['produto_id'])
        if product is None:
            raise InputError('Produto ' + str(item['produto_id']) + ' não encontrado', business=True)
        if product['estoque'] < demand[item['produto_id']]:
            raise InputError('Estoque insuficiente para ' + product['nome'], business=True)
        try:
            total += product['preco'] * item['quantidade']
        except OverflowError as exc:
            raise InputError('Total inválido', business=True) from exc
        if not math.isfinite(total):
            raise InputError('Total inválido', business=True)
    orders = Orders(db)
    order_id = orders.create(user_id, total)
    for item in items:
        product = loaded[item['produto_id']]
        orders.add_item(order_id, item['produto_id'], item['quantidade'], product['preco'])
        products.consume(item['produto_id'], item['quantidade'])
    return {'pedido_id': order_id, 'total': total}
