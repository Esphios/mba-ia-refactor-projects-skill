PRODUCT_FIELDS = ('id','nome','descricao','preco','estoque','categoria','ativo','criado_em')
USER_FIELDS = ('id','nome','email','tipo','criado_em')


def product(row):
    return {key: row[key] for key in PRODUCT_FIELDS} if row is not None else None


def user(row, login=False):
    fields = USER_FIELDS[:-1] if login else USER_FIELDS
    return {key: row[key] for key in fields} if row is not None else None
