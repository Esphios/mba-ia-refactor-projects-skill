from domain import sqlite_integer


class Orders:
    def __init__(self, db):
        self.db = db

    def create(self, user_id, total):
        return self.db.execute("INSERT INTO pedidos(usuario_id,status,total) VALUES(?,'pendente',?)", (user_id, total)).lastrowid

    def add_item(self, order_id, product_id, quantity, price):
        self.db.execute('INSERT INTO itens_pedido(pedido_id,produto_id,quantidade,preco_unitario) VALUES(?,?,?,?)',
            (order_id, product_id, quantity, price))

    def list(self, user_id=None):
        if user_id is not None and not sqlite_integer(user_id):
            return []
        where = '' if user_id is None else ' WHERE o.usuario_id=?'
        values = () if user_id is None else (user_id,)
        query = ('''SELECT o.id,o.usuario_id,o.status,o.total,o.criado_em,
            i.id AS item_id,i.produto_id,p.id AS related_product_id,p.nome AS produto_nome,
            i.quantidade,i.preco_unitario FROM pedidos o
            LEFT JOIN itens_pedido i ON i.pedido_id=o.id
            LEFT JOIN produtos p ON p.id=i.produto_id''' + where + ' ORDER BY o.id,i.id')
        orders, by_id = [], {}
        for row in self.db.execute(query, values):
            order = by_id.get(row['id'])
            if order is None:
                order = {field:row[field] for field in ('id','usuario_id','status','total','criado_em')}
                order['itens'] = []
                by_id[row['id']] = order
                orders.append(order)
            if row['item_id'] is not None:
                order['itens'].append({'produto_id':row['produto_id'],
                    'produto_nome':row['produto_nome'] if row['related_product_id'] is not None else 'Desconhecido',
                    'quantidade':row['quantidade'],'preco_unitario':row['preco_unitario']})
        return orders

    def update_status(self, order_id, status):
        if not sqlite_integer(order_id):
            return
        self.db.execute('UPDATE pedidos SET status=? WHERE id=?', (status, order_id))

    def totals(self):
        return self.db.execute("SELECT COUNT(*),SUM(total),SUM(status='pendente'),SUM(status='aprovado'),SUM(status='cancelado') FROM pedidos").fetchone()
