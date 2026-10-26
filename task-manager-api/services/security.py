"""Verified identity and controlled legacy-password migration."""
from datetime import datetime
from functools import wraps
import hashlib
import hmac
import re

from flask import current_app, g, request
from itsdangerous import BadData, URLSafeTimedSerializer
from werkzeug.security import check_password_hash
from models import store
from models.user import User
from utils.domain import utcnow
from utils.errors import ApiError


def signer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt='task-manager-access')


def credential_version(user):
    """Bind a token to this persisted account instance and credential."""
    key = current_app.config['SECRET_KEY']
    if isinstance(key, str):
        key = key.encode('utf-8')
    elif not isinstance(key, bytes):
        key = str(key).encode('utf-8')
    identity_material = f'{user.id}\0{user.email}\0{user.password}'.encode('utf-8')
    return hmac.new(key, identity_material, hashlib.sha256).hexdigest()


def issue_token(user):
    return signer().dumps({'user_id': user.id, 'credential': credential_version(user)})


def identity(optional=False):
    if hasattr(g, 'identity'):
        return g.identity
    header = request.headers.get('Authorization', '')
    if not header and optional:
        return None
    if not header.startswith('Bearer '):
        raise ApiError('Não autenticado', 401)
    try:
        payload = signer().loads(header[7:], max_age=current_app.config['TOKEN_MAX_AGE'])
        identifier = payload['user_id']
        credential = payload['credential']
        if type(identifier) is not int:
            raise ValueError('invalid identity')
        if not isinstance(credential, str):
            raise ValueError('invalid credential')
    except (BadData, KeyError, TypeError, ValueError):
        raise ApiError('Token inválido ou expirado', 401) from None
    user = store.get(User, identifier)
    if user is None:
        raise ApiError('Não autenticado', 401)
    if not hmac.compare_digest(credential, credential_version(user)):
        raise ApiError('Não autenticado', 401)
    if not user.active:
        raise ApiError('Usuário inativo', 403)
    g.identity = user
    return user


def require(*roles):
    def decorate(handler):
        @wraps(handler)
        def wrapped(*args, **kwargs):
            user = identity()
            if roles and user.role not in roles:
                raise ApiError('Acesso negado', 403)
            return handler(*args, **kwargs)
        return wrapped
    return decorate


def own_user(identifier):
    user = identity()
    if user.role not in ('admin', 'manager') and user.id != identifier:
        raise ApiError('Acesso negado', 403)


def own_task(task):
    user = identity()
    if user.role not in ('admin', 'manager') and task.user_id != user.id:
        raise ApiError('Acesso negado', 403)


def scope():
    user = identity()
    return None if user.role in ('admin', 'manager') else user.id


def verify_password(user, password):
    stored = user.password
    if re.fullmatch(r'[a-fA-F0-9]{32}', stored):
        cutoff = current_app.config.get('LEGACY_MD5_CUTOFF')
        now = current_app.config.get('CLOCK', utcnow)()
        if not cutoff or now >= datetime.fromisoformat(cutoff):
            return False
        valid = hmac.compare_digest(stored.lower(), hashlib.md5(password.encode('utf-8')).hexdigest())
        if valid:
            user.set_password(password)
            store.save()
        return valid
    try:
        return check_password_hash(stored, password)
    except (ValueError, TypeError):
        return False
