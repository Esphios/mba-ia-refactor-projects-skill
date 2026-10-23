import hashlib
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
import pytest
from sqlalchemy import event
from sqlalchemy.exc import SQLAlchemyError
from database import db
from models import User, Task, Category
from utils.dates import overdue, utc_naive
from app import create_app


def test_all_22_method_paths_success(client,tokens):
    a=tokens['admin'];o=tokens['owner']
    cases=[('get','/',None,None,200),('get','/health',None,None,200),
    ('get','/tasks',None,o,200),('get','/tasks/1',None,o,200),
    ('post','/tasks',{'title':'Created task','user_id':2},o,201),
    ('put','/tasks/1',{'title':'Updated task'},o,200),
    ('get','/tasks/search?q=Updated',None,o,200),('get','/tasks/stats',None,o,200),
    ('get','/users',None,a,200),('get','/users/2',None,o,200),
    ('post','/users',{'name':'New','email':'new@example.com','password':'password'},None,201),
    ('put','/users/2',{'name':'Changed'},o,200),('get','/users/2/tasks',None,o,200),
    ('post','/login',{'email':'owner@example.com','password':'password'},None,200),
    ('get','/reports/summary',None,a,200),('get','/reports/user/2',None,o,200),
    ('get','/categories',None,o,200),('post','/categories',{'name':'Extra'},a,201),
    ('put','/categories/2',{'name':'Updated'},a,200),('delete','/categories/2',None,a,200),
    ('delete','/tasks/1',None,o,200),('delete','/users/4',None,a,200)]
    for method,path,data,headers,status in cases:
        response=client.open(path,method=method.upper(),json=data,headers=headers or {})
        assert response.status_code==status,(method,path,response.json)
        assert 'password' not in str(response.json)

@pytest.mark.parametrize('method,path', [('GET','/tasks'),('GET','/tasks/1'),('POST','/tasks'),('PUT','/tasks/1'),('DELETE','/tasks/1'),('GET','/tasks/search'),('GET','/tasks/stats'),('GET','/users'),('GET','/users/2'),('PUT','/users/2'),('DELETE','/users/2'),('GET','/users/2/tasks'),('GET','/reports/summary'),('GET','/reports/user/2'),('GET','/categories'),('POST','/categories'),('PUT','/categories/1'),('DELETE','/categories/1')])
def test_protected_routes_deny_anonymous(client,method,path):
    response=client.open(path,method=method,json={'name':'Attempt','title':'Attempt'})
    assert response.status_code==401

@pytest.mark.parametrize('method,path', [('GET','/tasks/1'),('PUT','/tasks/1'),('DELETE','/tasks/1'),('GET','/users/2'),('PUT','/users/2'),('DELETE','/users/2'),('GET','/users/2/tasks'),('GET','/reports/user/2'),('GET','/users'),('GET','/reports/summary'),('POST','/categories'),('PUT','/categories/1'),('DELETE','/categories/1')])
def test_non_owner_and_non_admin_denied(client,tokens,method,path):
    response=client.open(path,method=method,json={'title':'Attempt','name':'Attempt'},headers=tokens['other'])
    assert response.status_code==403

def test_identity_filter_and_admin_access(client,tokens):
    assert client.get('/tasks',headers=tokens['other']).json==[]
    assert client.get('/tasks/search',headers=tokens['other']).json==[]
    assert client.get('/tasks/stats',headers=tokens['other']).json['total']==0
    assert client.get('/tasks/1',headers=tokens['admin']).status_code==200
    assert client.put('/tasks/1',json={'priority':1},headers=tokens['admin']).status_code==200
    assert client.get('/users/2',headers=tokens['admin']).status_code==200
    assert client.get('/reports/user/2',headers=tokens['admin']).status_code==200
    assert client.post('/tasks',json={'title':'Cross task','user_id':3},headers=tokens['owner']).status_code==403

def test_privilege_escalation(client,tokens):
    for role in ('admin','manager'):
        assert client.post('/users',json=dict(name='Bad',email='bad@example.com',password='password',role=role)).status_code==403
        assert client.put('/users/2',json={'role':role},headers=tokens['owner']).status_code==403
    assert client.put('/users/2',json={'active':False},headers=tokens['owner']).status_code==403
    assert client.put('/users/2',json={'role':'manager'},headers=tokens['admin']).status_code==200

@pytest.mark.parametrize('fields',[{'title':3},{'title':'ab'},{'title':'a'*201},{'priority':'2'},{'priority':True},{'priority':0},{'priority':6},{'status':'wrong'},{'due_date':'2026-02-30'},{'due_date':'1/2/2026'},{'tags':[3]},{'tags':7},{'user_id':'2'},{'description':2}])
def test_shared_validation_rejects_create_update_without_mutation(client,tokens,fields):
    data={'title':'Valid task',**fields}
    assert client.post('/tasks',json=data,headers=tokens['owner']).status_code==400
    assert client.put('/tasks/1',json={'title':'Should not persist',**fields},headers=tokens['owner']).status_code==400
    assert client.get('/tasks/1',headers=tokens['owner']).json['title']=='Original task'

def test_boundaries_and_absence(client,tokens):
    for title in ('abc','x'*200):
        assert client.put('/tasks/1',json={'title':title},headers=tokens['owner']).status_code==200
    for path in ('/tasks/999','/users/999','/reports/user/999'):
        assert client.get(path,headers=tokens['admin']).status_code==404
    assert client.post('/tasks',json={'title':'Valid','category_id':999},headers=tokens['owner']).status_code==404
    for value in (None,[],3,'value'):
        assert client.post('/users',json=value).status_code==400
    assert client.get('/tasks/search?priority=bad',headers=tokens['owner']).status_code==400
    assert client.post('/login',json={'email':"' OR 1=1 --",'password':'password'}).status_code==401
    assert client.post('/users',json={'name':'Again','email':'owner@example.com','password':'password'}).status_code==409

def test_tokens_wrong_expired_inactive(client,tokens,app):
    token=tokens['owner']['Authorization']
    assert client.get('/tasks',headers={'Authorization':token+'corrupt'}).status_code==401
    assert client.get('/tasks',headers={'Authorization':'Bearer fake-jwt-token-2'}).status_code==401
    app.config['TOKEN_MAX_AGE']=-1
    assert client.get('/tasks',headers=tokens['owner']).status_code==401
    app.config['TOKEN_MAX_AGE']=3600
    with app.app_context():
        user=db.session.get(User,2);user.active=False;db.session.commit()
    assert client.get('/tasks',headers=tokens['owner']).status_code==401
    assert client.post('/login',json={'email':'owner@example.com','password':'password'}).status_code==403

def test_md5_upgrade_only_correct_active_before_cutoff(client,app):
    legacy=hashlib.md5(b'password').hexdigest()
    with app.app_context():
        user=db.session.get(User,2);user.password=legacy;db.session.commit()
    assert client.post('/login',json={'email':'owner@example.com','password':'wrong'}).status_code==401
    with app.app_context(): assert db.session.get(User,2).password==legacy
    app.config['LEGACY_MD5_CUTOFF']='2000-01-01T00:00:00+00:00'
    assert client.post('/login',json={'email':'owner@example.com','password':'password'}).status_code==401
    app.config['LEGACY_MD5_CUTOFF']='2099-01-01T00:00:00+00:00'
    with app.app_context():
        u=db.session.get(User,2);u.active=False;db.session.commit()
    assert client.post('/login',json={'email':'owner@example.com','password':'password'}).status_code==403
    with app.app_context():
        u=db.session.get(User,2);assert u.password==legacy;u.active=True;db.session.commit()
    assert client.post('/login',json={'email':'owner@example.com','password':'password'}).status_code==200
    with app.app_context(): assert db.session.get(User,2).password.startswith('scrypt:')
    assert client.post('/login',json={'email':'owner@example.com','password':'password'}).status_code==200

def test_salted_passwords_and_responses(client,tokens,app):
    with app.app_context():
        assert db.session.get(User,1).password!=db.session.get(User,2).password
    for path in ('/users','/users/2','/reports/user/2'):
        payload=client.get(path,headers=tokens['admin']).get_data(as_text=True)
        assert 'scrypt:' not in payload and 'password' not in payload

def test_commit_failure_rolls_back_create_and_multi_delete(client,tokens,app):
    with patch.object(db.session,'commit',side_effect=SQLAlchemyError('secret sentinel')):
        response=client.post('/tasks',json={'title':'No persistence'},headers=tokens['owner'])
        assert response.status_code==500 and 'sentinel' not in response.get_data(as_text=True)
        response=client.delete('/users/2',headers=tokens['admin'])
        assert response.status_code==500
    with app.app_context():
        assert db.session.get(User,2) is not None
        assert db.session.get(Task,1) is not None
        assert len(list(db.session.scalars(db.select(Task))))==1

def test_relationship_deletion_policy(client,tokens,app):
    assert client.delete('/categories/1',headers=tokens['admin']).status_code==200
    with app.app_context(): assert db.session.get(Task,1).category_id is None
    assert client.delete('/users/2',headers=tokens['owner']).status_code==200
    with app.app_context(): assert db.session.get(Task,1) is None

def test_date_boundaries_naive_and_aware():
    now=datetime(2026,1,2,tzinfo=timezone.utc)
    task=Task(status='pending',due_date=now)
    assert not overdue(task,now)
    task.due_date=now-timedelta(seconds=1);assert overdue(task,now)
    task.due_date=now.replace(tzinfo=None)-timedelta(seconds=1);assert overdue(task,now)
    for status in ('done','cancelled'):
        task.status=status;assert not overdue(task,now)
    assert utc_naive(now)==datetime(2026,1,2)

def test_query_count_bounded(client,tokens,app):
    endpoints=['/tasks','/users','/categories','/reports/summary']
    def measure(path):
        statements=[]
        def capture(conn,cursor,statement,parameters,context,executemany):
            if statement.lstrip().upper().startswith('SELECT'): statements.append(statement)
        with app.app_context():
            event.listen(db.engine,'before_cursor_execute',capture)
            try: assert client.get(path,headers=tokens['admin']).status_code==200
            finally: event.remove(db.engine,'before_cursor_execute',capture)
        return len(statements)
    before={p:measure(p) for p in endpoints}
    with app.app_context():
        for index in range(20):
            u=User(name='Bulk',email=f'bulk{index}@example.com',password='unused');c=Category(name='Bulk');db.session.add_all([u,c]);db.session.flush();db.session.add(Task(title='Bulk task',user_id=u.id,category_id=c.id))
        db.session.commit()
    after={p:measure(p) for p in endpoints}
    print('QUERY_COUNTS',before,after)
    assert before==after
    assert after['/tasks']<=2 and after['/reports/summary']<=6

def test_legacy_database_copy_preserved(tmp_path):
    import sqlite3, shutil
    original=tmp_path/'legacy.db';copy=tmp_path/'copy.db'
    # Original schema and historical naive UTC values, built without new app startup.
    with sqlite3.connect(original) as conn:
        conn.executescript('CREATE TABLE users (id INTEGER PRIMARY KEY,name VARCHAR(100) NOT NULL,email VARCHAR(150) UNIQUE NOT NULL,password VARCHAR(255) NOT NULL,role VARCHAR(50),active BOOLEAN,created_at DATETIME); CREATE TABLE categories (id INTEGER PRIMARY KEY,name VARCHAR(100) NOT NULL,description VARCHAR(300),color VARCHAR(7),created_at DATETIME); CREATE TABLE tasks (id INTEGER PRIMARY KEY,title VARCHAR(200) NOT NULL,description TEXT,status VARCHAR(50),priority INTEGER,user_id INTEGER REFERENCES users(id),category_id INTEGER REFERENCES categories(id),created_at DATETIME,updated_at DATETIME,due_date DATETIME,tags VARCHAR(500));')
        conn.execute('INSERT INTO users VALUES (7,?,?,?,?,?,?)',('Legacy','legacy@example.com',hashlib.md5(b'password').hexdigest(),'user',1,'2020-01-01 00:00:00'))
        conn.execute("INSERT INTO categories VALUES (8,'Legacy category','','#000000','2020-01-01 00:00:00')")
        conn.execute("INSERT INTO tasks VALUES (9,'Historical task','','pending',2,7,8,'2020-01-01 00:00:00','2020-01-01 00:00:00','2020-01-02 00:00:00','old,retained')")
    original_bytes=original.read_bytes();shutil.copy2(original,copy)
    app=create_app(dict(TESTING=True,SECRET_KEY='copy-key',SQLALCHEMY_DATABASE_URI='sqlite:///'+str(copy),LEGACY_MD5_CUTOFF='2099-01-01T00:00:00+00:00'))
    c=app.test_client();response=c.post('/login',json={'email':'legacy@example.com','password':'password'});assert response.status_code==200
    task=c.get('/tasks/9',headers={'Authorization':'Bearer '+response.json['token']}).json
    assert task['due_date']=='2020-01-02 00:00:00' and task['created_at']=='2020-01-01 00:00:00' and task['overdue'] is True
    assert task['user_id']==7 and task['category_id']==8 and task['tags']==['old','retained']
    with app.app_context():
        assert db.session.get(User,7).password.startswith('scrypt:');assert db.session.get(Category,8).name=='Legacy category';db.session.remove();db.engine.dispose()
    assert original.read_bytes()==original_bytes

def test_notification_transport_is_mocked(monkeypatch):
    from services.notification_service import NotificationService
    monkeypatch.setenv('SMTP_ENABLED','true');monkeypatch.setenv('SMTP_HOST','smtp.invalid');monkeypatch.setenv('SMTP_USER','test@example.com');monkeypatch.setenv('SMTP_PASSWORD','not-real')
    transport=MagicMock();service=NotificationService(transport)
    assert service.send_email('recipient@example.com','Subject','Body') is True
    transport.assert_called_once_with('smtp.invalid',587,timeout=10)
    transport.return_value.__enter__.return_value.send_message.assert_called_once()
    monkeypatch.setenv('SMTP_ENABLED','false');transport.reset_mock();assert NotificationService(transport).send_email('recipient@example.com','S','B') is False;transport.assert_not_called()

def test_health_database_failure_sanitized(client):
    with patch.object(db.session,'execute',side_effect=SQLAlchemyError('secret sentinel')):
        response=client.get('/health');assert response.status_code==503;assert 'sentinel' not in response.get_data(as_text=True)


def test_success_response_shapes_preserved(client,tokens):
    base={'id','title','description','status','priority','user_id','category_id','created_at','updated_at','due_date','tags'}
    owner=tokens['owner'];admin=tokens['admin']
    assert set(client.get('/tasks',headers=owner).json[0])==base|{'overdue','user_name','category_name'}
    assert set(client.get('/tasks/1',headers=owner).json)==base|{'overdue'}
    assert set(client.get('/tasks/search',headers=owner).json[0])==base
    assert set(client.get('/users/2/tasks',headers=owner).json[0])=={'id','title','description','status','priority','created_at','due_date','overdue'}
    public_user={'id','name','email','role','active','created_at'}
    assert set(client.get('/users',headers=admin).json[0])==public_user|{'task_count'}
    assert set(client.get('/users/2',headers=owner).json)==public_user|{'tasks'}
    assert set(client.post('/login',json={'email':'owner@example.com','password':'password'}).json)=={'message','user','token'}
    assert set(client.get('/reports/summary',headers=admin).json)=={'generated_at','overview','tasks_by_status','tasks_by_priority','overdue','recent_activity','user_productivity'}
    assert set(client.get('/reports/user/2',headers=owner).json)=={'user','statistics'}
    assert set(client.get('/categories',headers=owner).json[0])=={'id','name','description','color','created_at','task_count'}


def test_seed_refuses_existing_database_and_preserves_records(app):
    import os, subprocess, sys
    from pathlib import Path
    env=os.environ.copy();env.update(SECRET_KEY='seed-check-key',DATABASE_URL=app.config['SQLALCHEMY_DATABASE_URI'],SEED_ADMIN_PASSWORD='temporary')
    result=subprocess.run([sys.executable,'seed.py'],cwd=Path(__file__).resolve().parents[1],env=env,capture_output=True,text=True)
    assert result.returncode!=0 and 'banco não vazio' in result.stderr
    with app.app_context():
        assert len(list(db.session.scalars(db.select(User))))==3
        assert db.session.get(Task,1).title=='Original task'


def test_no_implicit_schema_or_data_mutation_on_factory(tmp_path):
    path=tmp_path/'not-created.db'
    app=create_app(dict(SECRET_KEY='factory-test',SQLALCHEMY_DATABASE_URI='sqlite:///'+str(path)))
    assert not path.exists()


def test_deprecation_paths_with_warnings_as_errors(client,tokens):
    import warnings
    from sqlalchemy.exc import LegacyAPIWarning
    with warnings.catch_warnings():
        warnings.simplefilter('error',LegacyAPIWarning)
        warnings.simplefilter('error',DeprecationWarning)
        assert client.get('/tasks/1',headers=tokens['owner']).status_code==200
        assert client.get('/reports/summary',headers=tokens['admin']).status_code==200


def test_search_preserves_sqlite_like_wildcards_case_and_owner(client,tokens,app):
    with app.app_context():
        db.session.add_all([
            Task(title='Alpha Demo',description='Résumé',user_id=2),
            Task(title='ALPHA SECOND',description='Other',user_id=2),
            Task(title='Secret Alpha',description='Hidden',user_id=3),
        ])
        db.session.commit()
    owner=tokens['owner']
    def titles(query,headers=owner):
        response=client.get('/tasks/search',query_string={'q':query},headers=headers)
        assert response.status_code==200
        return {row['title'] for row in response.json}
    assert titles('%')=={'Original task','Alpha Demo','ALPHA SECOND'}
    assert titles('_')=={'Original task','Alpha Demo','ALPHA SECOND'}
    assert titles('alpha')=={'Alpha Demo','ALPHA SECOND'}
    assert titles('ALPHA')=={'Alpha Demo','ALPHA SECOND'}
    assert titles('rÉsumÉ')==set()  # SQLite LIKE folds ASCII only by default.
    assert titles('Résumé')=={'Alpha Demo'}
    assert titles('Secret')==set()
    assert titles('Secret',tokens['admin'])=={'Secret Alpha'}
    assert titles("%' OR 1=1 --")==set()


def test_create_description_defaults_and_explicit_null_preserved(client,tokens):
    for path,payload,headers in [('/tasks',{'title':'Default description'},tokens['owner']),('/categories',{'name':'Default description'},tokens['admin'])]:
        response=client.post(path,json=payload,headers=headers)
        assert response.status_code==201
        assert response.json['description']==''
        explicit=client.post(path,json={**payload,'description':None},headers=headers)
        assert explicit.status_code==201 and explicit.json['description'] is None


def test_error_messages_preserve_exact_portuguese_unicode(client,tokens):
    malformed=client.post('/users',json=[])
    assert malformed.status_code==400
    assert malformed.json=={'error':'Dados inv\u00e1lidos'}
    filtered=client.get('/tasks/search?priority=bad',headers=tokens['owner'])
    assert filtered.status_code==400
    assert filtered.json=={'error':'Filtro inv\u00e1lido'}
    missing=client.get('/tasks/999',headers=tokens['admin'])
    assert missing.status_code==404
    assert missing.json=={'error':'Recurso n\u00e3o encontrado'}
