import math
from domain import CATEGORIES, DEFAULT_CATEGORY, SQLITE_MAX_INTEGER


class InputError(ValueError):
    def __init__(self, message='Dados inválidos', business=False):
        super().__init__(message)
        self.business = business


def payload(value, allow_empty=False):
    if not isinstance(value, dict) or (not value and not allow_empty):
        raise InputError()
    return value


def text(value, message='Dados inválidos'):
    if not isinstance(value, str):
        raise InputError(message)
    return value


def integer(value, positive=True):
    if type(value) is not int or not (1 if positive else 0) <= value <= 9223372036854775807:
        raise InputError()
    return value


def number(value):
    if type(value) not in (int, float):
        raise InputError()
    try:
        valid = math.isfinite(value)
    except OverflowError:
        valid = False
    if not valid:
        raise InputError()
    if type(value) is int and not -SQLITE_MAX_INTEGER - 1 <= value <= SQLITE_MAX_INTEGER:
        converted = float(value)
        if not math.isfinite(converted):
            raise InputError()
        return converted
    return value


def product(value):
    value = payload(value)
    for key, message in [('nome','Nome é obrigatório'),('preco','Preço é obrigatório'),('estoque','Estoque é obrigatório')]:
        if key not in value:
            raise InputError(message)
    name, description = text(value['nome']), text(value.get('descricao', ''))
    price, stock = number(value['preco']), value['estoque']
    if price < 0:
        raise InputError('Preço não pode ser negativo')
    if type(stock) in (int, float) and stock < 0:
        raise InputError('Estoque não pode ser negativo')
    integer(stock, positive=False)
    if len(name) < 2:
        raise InputError('Nome muito curto')
    if len(name) > 200:
        raise InputError('Nome muito longo')
    category = value.get('categoria', DEFAULT_CATEGORY)
    if category not in CATEGORIES:
        raise InputError('Categoria inválida. Válidas: ' + str(list(CATEGORIES)))
    return name, description, price, stock, category


def credentials(value, registering=False):
    value = payload(value, allow_empty=not registering)
    email, password = value.get('email',''), value.get('senha','')
    name = value.get('nome','') if registering else ''
    if not email or not password or (registering and not name):
        raise InputError('Nome, email e senha são obrigatórios' if registering else 'Email e senha são obrigatórios')
    text(email); text(password)
    if registering:
        text(name)
    return name, email, password


def order(value):
    value = payload(value)
    user_id = value.get('usuario_id')
    if not user_id:
        raise InputError('Usuario ID é obrigatório')
    integer(user_id)
    items = value.get('itens', [])
    if not isinstance(items, list) or not items:
        raise InputError('Pedido deve ter pelo menos 1 item')
    for item in items:
        if not isinstance(item, dict):
            raise InputError()
        integer(item.get('produto_id')); integer(item.get('quantidade'))
    return user_id, items


def search_bound(value):
    if value is None or value == '':
        return None
    try:
        return number(float(value))
    except (ValueError, TypeError, OverflowError) as exc:
        raise InputError() from exc
