from database import get_db


class SystemModel:
    def counts(self):
        row = get_db().execute("""
            SELECT
              (SELECT COUNT(*) FROM produtos) AS produtos,
              (SELECT COUNT(*) FROM usuarios) AS usuarios,
              (SELECT COUNT(*) FROM pedidos) AS pedidos
        """).fetchone()
        return dict(row)
