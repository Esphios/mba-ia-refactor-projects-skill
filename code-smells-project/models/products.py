import serializers
from domain import sqlite_integer


class Products:
    def __init__(self, db):
        self.db = db

    def all(self):
        return [serializers.product(row) for row in self.db.execute('SELECT * FROM produtos ORDER BY id')]

    def get(self, product_id):
        if not sqlite_integer(product_id):
            return None
        return serializers.product(self.db.execute('SELECT * FROM produtos WHERE id=?', (product_id,)).fetchone())

    def create(self, values):
        return self.db.execute('INSERT INTO produtos(nome,descricao,preco,estoque,categoria) VALUES(?,?,?,?,?)', values).lastrowid

    def update(self, product_id, values):
        self.db.execute('UPDATE produtos SET nome=?,descricao=?,preco=?,estoque=?,categoria=? WHERE id=?', (*values, product_id))

    def delete(self, product_id):
        self.db.execute('DELETE FROM produtos WHERE id=?', (product_id,))

    def search(self, term, category, minimum, maximum):
        query, values = 'SELECT * FROM produtos WHERE 1=1', []
        if term:
            query += ' AND (nome LIKE ? OR descricao LIKE ?)'
            values += ['%' + term + '%', '%' + term + '%']
        if category:
            query += ' AND categoria=?'
            values.append(category)
        # Preserve original truthiness for zero bounds and SQLite LIKE semantics.
        if minimum:
            query += ' AND preco>=?'
            values.append(minimum)
        if maximum:
            query += ' AND preco<=?'
            values.append(maximum)
        return [serializers.product(row) for row in self.db.execute(query + ' ORDER BY id', values)]

    def by_ids(self, ids):
        placeholders = ','.join('?' for _ in ids)
        return {row['id']: row for row in self.db.execute('SELECT * FROM produtos WHERE id IN (' + placeholders + ')', ids)}

    def consume(self, product_id, quantity):
        self.db.execute('UPDATE produtos SET estoque=estoque-? WHERE id=?', (quantity, product_id))
