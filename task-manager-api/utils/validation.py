import re
from datetime import datetime
from errors import APIError
from utils.constants import STATUSES, PRIORITIES, MIN_TITLE_LENGTH, MAX_TITLE_LENGTH, ROLES

def body(value):
    if not isinstance(value,dict) or not value: raise APIError('Dados inválidos')
    return value

def text(value,field,minimum=1,maximum=10000,nullable=False):
    if nullable and value is None: return value
    if not isinstance(value,str) or not minimum<=len(value)<=maximum: raise APIError('Campo inválido: '+field)
    return value

def integer(value,field):
    if type(value) is not int or value<1: raise APIError('Campo inválido: '+field)
    return value

def task_fields(data,create=False):
    result={}
    if create or 'title' in data: result['title']=text(data.get('title'),'title',MIN_TITLE_LENGTH,MAX_TITLE_LENGTH)
    if create: result['description']=''
    if 'description' in data: result['description']=text(data['description'],'description',0,nullable=True)
    if 'status' in data:
        if data['status'] not in STATUSES: raise APIError('Status inválido')
        result['status']=data['status']
    if 'priority' in data:
        if type(data['priority']) is not int or data['priority'] not in PRIORITIES: raise APIError('Prioridade inválida')
        result['priority']=data['priority']
    for key in ('user_id','category_id'):
        if key in data: result[key]=integer(data[key],key) if data[key] is not None else None
    if 'due_date' in data:
        value=data['due_date']
        try:
            if value is not None and (not isinstance(value,str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',value)): raise ValueError()
            result['due_date']=datetime.strptime(value,'%Y-%m-%d') if value else None
        except ValueError: raise APIError('Formato de data inválido. Use YYYY-MM-DD')
    if 'tags' in data:
        tags=data['tags']
        if isinstance(tags,list):
            if not all(isinstance(t,str) and ',' not in t for t in tags): raise APIError('Tags inválidas')
            tags=','.join(tags)
        if tags is not None: text(tags,'tags',0,500)
        result['tags']=tags
    return result

def user_fields(data,create=False):
    result={}
    for key in ('name','email','password'):
        if create or key in data:
            value=text(data.get(key),key,4 if key=='password' else 1,150 if key=='email' else 10000 if key=='password' else 100)
            if key=='email' and not re.fullmatch(r'[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+',value): raise APIError('Email inválido')
            result[key]=value
    if 'role' in data:
        if data['role'] not in ROLES: raise APIError('Role inválido')
        result['role']=data['role']
    if 'active' in data:
        if type(data['active']) is not bool: raise APIError('Active inválido')
        result['active']=data['active']
    return result

def category_fields(data,create=False):
    result={}
    if create or 'name' in data: result['name']=text(data.get('name'),'name',1,100)
    if create: result['description']=''
    if 'description' in data: result['description']=text(data['description'],'description',0,300,True)
    if 'color' in data:
        if not isinstance(data['color'],str) or not re.fullmatch(r'#[0-9a-fA-F]{6}',data['color']): raise APIError('Cor inválida')
        result['color']=data['color']
    return result
