from math import isfinite

from errors import APIError


VALID_CATEGORIES = (
    "informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"
)


def validate_product(payload):
    if not isinstance(payload, dict):
        raise APIError("Dados inválidos")
    for field, message in (
        ("nome", "Nome é obrigatório"),
        ("preco", "Preço é obrigatório"),
        ("estoque", "Estoque é obrigatório"),
    ):
        if field not in payload:
            raise APIError(message)

    name = payload["nome"]
    price = payload["preco"]
    stock = payload["estoque"]
    category = payload.get("categoria", "geral")
    if not isinstance(name, str) or len(name) < 2:
        raise APIError("Nome muito curto")
    if len(name) > 200:
        raise APIError("Nome muito longo")
    if isinstance(price, bool) or not isinstance(price, (int, float)) or price < 0:
        raise APIError("Preço não pode ser negativo")
    try:
        finite_price = isfinite(price)
    except OverflowError:
        finite_price = False
    if not finite_price:
        raise APIError('Preço deve ser um número finito')
    if isinstance(stock, bool) or not isinstance(stock, int) or stock < 0:
        raise APIError("Estoque não pode ser negativo")
    if category not in VALID_CATEGORIES:
        raise APIError(f"Categoria inválida. Válidas: {list(VALID_CATEGORIES)}")
    return {
        "nome": name,
        "descricao": payload.get("descricao", ""),
        "preco": price,
        "estoque": stock,
        "categoria": category,
    }
