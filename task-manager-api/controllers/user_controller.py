from models import store
from models.user import User
from services.security import identity, issue_token, own_user, verify_password
from utils import validation
from utils.domain import overdue
from utils.errors import ApiError


def find(user_id):
    user = store.get(User, user_id)
    if user is None:
        raise ApiError('Usuário não encontrado', 404)
    return user


def get_users():
    return [{**user.to_dict(), 'task_count': count} for user, count in store.users()], 200


def get_user(user_id):
    own_user(user_id)
    user = find(user_id)
    return {**user.to_dict(), 'tasks': [task.to_dict() for task in store.tasks(user_id=user_id)]}, 200


def create_user(data):
    values = validation.user_data(data, create=True)
    actor = identity(optional=True)
    if values.get('role', 'user') != 'user' and (actor is None or actor.role != 'admin'):
        raise ApiError('Acesso negado', 403)
    if store.email_user(values['email']):
        raise ApiError('Email já cadastrado', 409)
    user = User(name=values['name'], email=values['email'], role=values.get('role', 'user'))
    user.set_password(values['password'])
    # active was never a creation input; preserve that contract.
    store.save(user)
    return user.to_dict(), 201


def update_user(user_id, data):
    actor = identity()
    if actor.role != 'admin' and actor.id != user_id:
        raise ApiError('Acesso negado', 403)
    user = find(user_id)
    values = validation.user_data(data)
    if actor.role != 'admin' and any(key in values for key in ('role', 'active')):
        raise ApiError('Acesso negado', 403)
    if 'email' in values:
        existing = store.email_user(values['email'])
        if existing and existing.id != user_id:
            raise ApiError('Email já cadastrado', 409)
    for key, value in values.items():
        if key == 'password':
            user.set_password(value)
        else:
            setattr(user, key, value)
    store.save()
    return user.to_dict(), 200


def delete_user(user_id):
    store.delete_user(find(user_id))
    return {'message': 'Usuário deletado com sucesso'}, 200


def get_user_tasks(user_id):
    own_user(user_id)
    find(user_id)
    result = []
    for task in store.tasks(user_id=user_id):
        data = task.to_dict()
        result.append({**{key: data[key] for key in ('id', 'title', 'description', 'status', 'priority', 'created_at', 'due_date')},
            'overdue': overdue(task)})
    return result, 200


def login(data):
    validation.object_data(data)
    email, password = data.get('email'), data.get('password')
    if not email or not password:
        raise ApiError('Email e senha são obrigatórios')
    validation.text(email)
    validation.text(password)
    user = store.email_user(email)
    if not user:
        raise ApiError('Credenciais inválidas', 401)
    # Do not upgrade passwords for disabled accounts.
    if not user.active:
        # Existing response status for a disabled account with a modern correct password.
        if not user.check_password(password):
            raise ApiError('Credenciais inválidas', 401)
        raise ApiError('Usuário inativo', 403)
    if not verify_password(user, password):
        raise ApiError('Credenciais inválidas', 401)
    return {'message': 'Login realizado com sucesso', 'user': user.to_dict(), 'token': issue_token(user)}, 200
