from database import get_db


class AdminModel:
    def reset_database(self):
        connection = get_db()
        try:
            connection.execute("BEGIN")
            connection.execute("DELETE FROM itens_pedido")
            connection.execute("DELETE FROM pedidos")
            connection.execute("DELETE FROM produtos")
            connection.execute("DELETE FROM usuarios")
            connection.commit()
        except Exception:
            connection.rollback()
            raise

    def execute(self, sql):
        connection = get_db()
        cursor = connection.execute(sql)
        if sql.lstrip().upper().startswith("SELECT"):
            return [dict(row) for row in cursor.fetchall()], False
        connection.commit()
        return None, True
