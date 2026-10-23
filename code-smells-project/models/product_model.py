from database import get_db


PRODUCT_FIELDS = (
    "id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em"
)


def serialize_product(row):
    return {field: row[field] for field in PRODUCT_FIELDS}


class ProductModel:
    def list_all(self):
        rows = get_db().execute("SELECT * FROM produtos ORDER BY id").fetchall()
        return [serialize_product(row) for row in rows]

    def find(self, product_id):
        row = get_db().execute(
            "SELECT * FROM produtos WHERE id = ?", (product_id,)
        ).fetchone()
        return serialize_product(row) if row else None

    def search(self, term="", category=None, minimum=None, maximum=None):
        query = "SELECT * FROM produtos WHERE 1 = 1"
        parameters = []
        if term:
            query += " AND (nome LIKE ? OR descricao LIKE ?)"
            wildcard = f"%{term}%"
            parameters.extend([wildcard, wildcard])
        if category:
            query += " AND categoria = ?"
            parameters.append(category)
        if minimum is not None:
            query += " AND preco >= ?"
            parameters.append(minimum)
        if maximum is not None:
            query += " AND preco <= ?"
            parameters.append(maximum)
        query += " ORDER BY id"
        rows = get_db().execute(query, parameters).fetchall()
        return [serialize_product(row) for row in rows]

    def create(self, values):
        cursor = get_db().execute(
            """
            INSERT INTO produtos (nome, descricao, preco, estoque, categoria)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                values["nome"], values["descricao"], values["preco"],
                values["estoque"], values["categoria"],
            ),
        )
        get_db().commit()
        return cursor.lastrowid

    def update(self, product_id, values):
        get_db().execute(
            """
            UPDATE produtos
            SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ?
            WHERE id = ?
            """,
            (
                values["nome"], values["descricao"], values["preco"],
                values["estoque"], values["categoria"], product_id,
            ),
        )
        get_db().commit()

    def is_referenced(self, product_id):
        return get_db().execute(
            "SELECT 1 FROM itens_pedido WHERE produto_id = ? LIMIT 1", (product_id,)
        ).fetchone() is not None

    def delete(self, product_id):
        get_db().execute("DELETE FROM produtos WHERE id = ?", (product_id,))
        get_db().commit()

