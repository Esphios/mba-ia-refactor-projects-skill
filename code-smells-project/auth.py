"""Signed expiring Bearer credentials; database identity/role stays authoritative."""
import hmac
from datetime import datetime, timezone
from functools import wraps

from flask import current_app, g, jsonify, request
from itsdangerous import BadData, URLSafeSerializer
from werkzeug.security import check_password_hash, generate_password_hash

from database import get_db, transaction
from models.users import Users


def now():
    return current_app.config['CLOCK']().astimezone(timezone.utc)


def signer():
    return URLSafeSerializer(current_app.config['SECRET_KEY'], salt='shop-access-v1')


def issue_token(user_id):
    issued = now().timestamp()
    return signer().dumps({'uid': user_id, 'iat': issued, 'exp': issued + current_app.config['TOKEN_TTL']})


def login(email, password):
    with transaction() as db:
        users = Users(db)
        for row in users.by_email(email):
            if not isinstance(row['senha'], str):
                continue
            stored = row['senha']
            modern = stored.startswith(('scrypt:', 'pbkdf2:'))
            if modern:
                try:
                    valid = check_password_hash(stored, password)
                except (ValueError, TypeError):
                    valid = False
            else:
                cutoff = current_app.config['LEGACY_PASSWORD_CUTOFF']
                valid = bool(cutoff and now() < datetime.fromisoformat(cutoff)
                    and hmac.compare_digest(stored.encode('utf-8'), password.encode('utf-8')))
            if not valid:
                continue
            if not modern:
                users.upgrade_password(row['id'], generate_password_hash(password))
            return row
        return None


def require_identity(admin=False, owner_parameter=None):
    def decorate(handler):
        @wraps(handler)
        def protected(*args, **kwargs):
            authorization = request.headers.get('Authorization', '')
            scheme, _, token = authorization.partition(' ')
            if scheme.lower() != 'bearer' or not token:
                return jsonify({'erro': 'Não autenticado'}), 401
            try:
                claims = signer().loads(token)
                timestamp = now().timestamp()
                if (not isinstance(claims, dict) or type(claims.get('uid')) is not int
                    or type(claims.get('exp')) not in (int, float)
                    or type(claims.get('iat')) not in (int, float)
                    or not claims['iat'] <= timestamp < claims['exp']):
                    raise ValueError('Invalid claims')
                identity = Users(get_db()).get(claims['uid'])
                if identity is None:
                    raise ValueError('Missing identity')
            except (BadData, ValueError, TypeError, KeyError):
                return jsonify({'erro': 'Não autenticado'}), 401
            g.identity = identity
            is_admin = identity['tipo'] == 'admin'
            if admin and not is_admin:
                return jsonify({'erro': 'Acesso negado'}), 403
            if owner_parameter and not is_admin and kwargs[owner_parameter] != identity['id']:
                return jsonify({'erro': 'Acesso negado'}), 403
            return handler(*args, **kwargs)
        return protected
    return decorate
