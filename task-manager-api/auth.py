from flask import current_app, request, g
from itsdangerous import URLSafeTimedSerializer, BadSignature
from database import db
from models.user import User
from errors import APIError

def signer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'],salt='task-manager-access')

def issue_token(user):
    return signer().dumps({'user_id':user.id})

def authenticate():
    header=request.headers.get('Authorization','')
    if not header.startswith('Bearer '): raise APIError('Autenticação obrigatória',401)
    try:
        payload=signer().loads(header[7:],max_age=current_app.config['TOKEN_MAX_AGE'])
        user=db.session.get(User,payload['user_id'])
    except (BadSignature,KeyError,TypeError,ValueError):
        raise APIError('Token inválido ou expirado',401)
    if not user or not user.active: raise APIError('Identidade inativa ou inválida',401)
    g.identity=user
    return user

def admin():
    user=authenticate()
    if not user.is_admin(): raise APIError('Acesso negado',403)
    return user

def owner(user_id):
    user=g.identity
    if user.id!=user_id and not user.is_admin(): raise APIError('Acesso negado',403)
