import hashlib
import hmac
import re
from datetime import datetime, timezone
from flask import g, current_app
from auth import authenticate, admin, owner, issue_token
from database import db
from models import User, Task
from models import repository as repo
from utils.validation import body, user_fields, text
from utils.serialization import task_data
from errors import APIError

def listing():
    admin()
    return [dict(u.to_dict(),task_count=len(u.tasks)) for u in repo.users()]

def detail(user_id):
    authenticate();owner(user_id);user=repo.get(User,user_id)
    return dict(user.to_dict(),tasks=[task_data(t) for t in repo.tasks(user_id)])

def write(data,user_id=None):
    data=body(data)
    if user_id:
        authenticate();owner(user_id);user=repo.get(User,user_id)
        if any(k in data for k in ('role','active')) and not g.identity.is_admin(): raise APIError('Acesso negado',403)
    else:
        if data.get('role','user')!='user' or data.get('active',True) is not True: raise APIError('Acesso negado',403)
        user=User()
    values=user_fields(data,not user_id)
    if 'email' in values:
        existing=repo.email_user(values['email'])
        if existing and existing.id!=user_id: raise APIError('Email já cadastrado',409)
    for key,value in values.items():
        if key=='password': user.set_password(value)
        else: setattr(user,key,value)
    return repo.save(user).to_dict()

def remove(user_id):
    authenticate();owner(user_id);user=repo.get(User,user_id)
    for task in repo.tasks(user_id): db.session.delete(task)
    repo.delete(user)
    return {'message':'Usuário deletado com sucesso'}

def tasks(user_id):
    authenticate();owner(user_id);repo.get(User,user_id)
    return [task_data(t,'user') for t in repo.tasks(user_id)]

def login(data):
    data=body(data);email=text(data.get('email'),'email');password=text(data.get('password'),'password')
    user=repo.email_user(email)
    if not user: raise APIError('Credenciais inválidas',401)
    legacy=bool(re.fullmatch(r'[0-9a-f]{32}',user.password or ''))
    if legacy:
        cutoff=datetime.fromisoformat(current_app.config['LEGACY_MD5_CUTOFF'])
        if cutoff.tzinfo is None: cutoff=cutoff.replace(tzinfo=timezone.utc)
        valid=datetime.now(timezone.utc)<cutoff and hmac.compare_digest(user.password,hashlib.md5(password.encode()).hexdigest())
    else: valid=user.check_password(password)
    if not valid: raise APIError('Credenciais inválidas',401)
    if not user.active: raise APIError('Usuário inativo',403)
    if legacy: user.set_password(password);repo.save(user)
    return dict(message='Login realizado com sucesso',user=user.to_dict(),token=issue_token(user))
