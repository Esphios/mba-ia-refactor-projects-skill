"""Validate approved types while retaining legacy defaults and messages."""
from datetime import datetime
import math
from utils.domain import MAX_TITLE, MIN_TITLE, MIN_PRIORITY, MAX_PRIORITY, MIN_PASSWORD, ROLES, STATUSES
from utils.errors import ApiError
from utils.helpers import validate_email


def object_data(data, allow_empty=False):
    if not isinstance(data, dict) or (not data and not allow_empty):
        raise ApiError('Dados inválidos')
    return data


def text(value, message='Dados inválidos', nullable=False):
    if value is None and nullable:
        return value
    if not isinstance(value, str):
        raise ApiError(message)
    return value


def user_data(data, create=False):
    object_data(data)
    fields = ('name', 'email', 'password', 'role') if create else ('name', 'email', 'password', 'role', 'active')
    result = {key: data[key] for key in fields if key in data}
    if create:
        for key, message in [('name', 'Nome é obrigatório'), ('email', 'Email é obrigatório'), ('password', 'Senha é obrigatória')]:
            if not data.get(key):
                raise ApiError(message)
    if 'name' in result:
        text(result['name'])
    if 'email' in result:
        email = text(result['email'], 'Email inválido')
        if not validate_email(email):
            raise ApiError('Email inválido')
    if 'password' in result:
        password = text(result['password'], 'Senha inválida')
        if len(password) < MIN_PASSWORD:
            raise ApiError('Senha deve ter no mínimo 4 caracteres' if create else 'Senha muito curta')
    if 'role' in result and result['role'] not in ROLES:
        raise ApiError('Role inválido')
    if 'active' in result and type(result['active']) is not bool:
        raise ApiError('Active inválido')
    return result


def task_data(data, create=False):
    object_data(data)
    result = {key: data[key] for key in ('title', 'description', 'status', 'priority', 'user_id', 'category_id', 'due_date', 'tags') if key in data}
    if create and not data.get('title'):
        raise ApiError('Título é obrigatório')
    if 'title' in result:
        title = text(result['title'], 'Título inválido')
        if len(title) < MIN_TITLE:
            raise ApiError('Título muito curto')
        if len(title) > MAX_TITLE:
            raise ApiError('Título muito longo')
    if 'description' in result:
        text(result['description'], nullable=True)
    if 'status' in result and result['status'] not in STATUSES:
        raise ApiError('Status inválido')
    if 'priority' in result:
        priority = result['priority']
        if type(priority) not in (int, float) or (type(priority) is float and not math.isfinite(priority)):
            raise ApiError('Prioridade inválida')
        if not MIN_PRIORITY <= priority <= MAX_PRIORITY:
            raise ApiError('Prioridade deve ser entre 1 e 5')
    for key in ('user_id', 'category_id'):
        if key in result and result[key] is not None and type(result[key]) is not int:
            raise ApiError('Identificador inválido')
    if 'due_date' in result:
        date = result['due_date']
        if date:
            try:
                result['due_date'] = datetime.strptime(date, '%Y-%m-%d')
            except (TypeError, ValueError):
                raise ApiError('Formato de data inválido. Use YYYY-MM-DD' if create else 'Formato de data inválido') from None
        else:
            if date not in (None, ''):
                raise ApiError('Formato de data inválido')
            result['due_date'] = None
    if 'tags' in result:
        tags = result['tags']
        if isinstance(tags, list):
            if any(not isinstance(tag, str) for tag in tags):
                raise ApiError('Tags inválidas')
            result['tags'] = ','.join(tags)
        elif tags is not None and not isinstance(tags, str):
            raise ApiError('Tags inválidas')
        if create and not tags:
            result.pop('tags')
    return result


def category_data(data, create=False):
    object_data(data, allow_empty=not create)
    if create and not data.get('name'):
        raise ApiError('Nome é obrigatório')
    result = {key: data[key] for key in ('name', 'description', 'color') if key in data}
    for key, value in result.items():
        text(value, nullable=key != 'name')
    return result


def search_data(args):
    filters = {key: args.get(key, '') for key in ('q', 'status', 'priority', 'user_id')}
    for key in ('priority', 'user_id'):
        if filters[key]:
            try:
                filters[key] = int(filters[key])
            except ValueError:
                raise ApiError('Filtro inválido') from None
    return filters
