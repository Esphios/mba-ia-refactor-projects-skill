class System:
    def __init__(self, db):
        self.db = db

    def counts(self):
        self.db.execute('SELECT 1')
        return {name: self.db.execute('SELECT COUNT(*) FROM ' + name).fetchone()[0]
            for name in ('produtos', 'usuarios', 'pedidos')}

    def reset(self):
        for table in ('itens_pedido', 'pedidos', 'produtos', 'usuarios'):
            self.db.execute('DELETE FROM ' + table)

    def query(self, sql):
        cursor = self.db.execute(sql)
        if sql.strip().upper().startswith('SELECT'):
            return [dict(row) for row in cursor.fetchall()]
        return None
