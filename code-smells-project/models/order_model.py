from database import get_db


ORDER_FIELDS = ("id", "usuario_id", "status", "total", "criado_em")


class OrderModel:
    def create(self, user_id, total):
        cursor = get_db().execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
            (user_id, total),
        )
        return cursor.lastrowid

    def add_item(self, order_id, item):
        get_db().execute(
            """
            INSERT INTO itens_pedido
                (pedido_id, produto_id, quantidade, preco_unitario)
            VALUES (?, ?, ?, ?)
            """,
            (order_id, item["produto_id"], item["quantidade"], item["preco_unitario"]),
        )

    def reduce_stock(self, product_id, quantity):
        cursor = get_db().execute(
            """
            UPDATE produtos SET estoque = estoque - ?
            WHERE id = ? AND estoque >= ?
            """,
            (quantity, product_id, quantity),
        )
        return cursor.rowcount == 1

    def find(self, order_id):
        row = get_db().execute(
            "SELECT * FROM pedidos WHERE id = ?", (order_id,)
        ).fetchone()
        return dict(row) if row else None

    def items_for_order(self, order_id):
        rows = get_db().execute(
            "SELECT produto_id, quantidade, preco_unitario FROM itens_pedido WHERE pedido_id = ?",
            (order_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def update_status(self, order_id, status):
        get_db().execute(
            "UPDATE pedidos SET status = ? WHERE id = ?", (status, order_id)
        )

    def restore_stock(self, items):
        get_db().executemany(
            "UPDATE produtos SET estoque = estoque + ? WHERE id = ?",
            [(item["quantidade"], item["produto_id"]) for item in items],
        )

    def list_orders(self, user_id=None):
        query = "SELECT * FROM pedidos"
        parameters = []
        if user_id is not None:
            query += " WHERE usuario_id = ?"
            parameters.append(user_id)
        query += " ORDER BY id"
        order_rows = get_db().execute(query, parameters).fetchall()
        orders = [
            {**{field: row[field] for field in ORDER_FIELDS}, "itens": []}
            for row in order_rows
        ]
        if not orders:
            return orders

        placeholders = ",".join("?" for _ in orders)
        item_rows = get_db().execute(
            f"""
            SELECT i.pedido_id, i.produto_id, p.nome AS produto_nome,
                   i.quantidade, i.preco_unitario
            FROM itens_pedido i
            LEFT JOIN produtos p ON p.id = i.produto_id
            WHERE i.pedido_id IN ({placeholders})
            ORDER BY i.id
            """,
            [order["id"] for order in orders],
        ).fetchall()
        by_id = {order["id"]: order for order in orders}
        for item in item_rows:
            by_id[item["pedido_id"]]["itens"].append({
                "produto_id": item["produto_id"],
                "produto_nome": item["produto_nome"] or "Desconhecido",
                "quantidade": item["quantidade"],
                "preco_unitario": item["preco_unitario"],
            })
        return orders

