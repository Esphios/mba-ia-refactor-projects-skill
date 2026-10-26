"""Approved changes: every expectation names an observable legacy defect."""
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import pytest
from werkzeug.security import check_password_hash, generate_password_hash
from conftest import rows


@pytest.mark.parametrize('method,path,body', [
    ('POST','/produtos',{'nome':'AA','preco':1,'estoque':1}),
    ('PUT','/produtos/1',{'nome':'AA','preco':1,'estoque':1}),
    ('DELETE','/produtos/1',None), ('GET','/usuarios',None),
    ('GET','/usuarios/2',None), ('GET','/pedidos',None),
    ('GET','/pedidos/usuario/2',None), ('POST','/pedidos',{'usuario_id':2,'itens':[{'produto_id':1,'quantidade':1}]}),
    ('PUT','/pedidos/1/status',{'status':'aprovado'}),
    ('GET','/relatorios/vendas',None), ('POST','/admin/query',{'sql':'SELECT 1'}),
    ('POST','/admin/reset-db',None)])
def test_sensitive_operations_require_verified_identity(shop,method,path,body):
    _,c,_,_=shop
    assert c.open(path,method=method,json=body).status_code == 401


def test_owner_admin_and_current_role_boundary(shop):
    _,c,path,h=shop
    assert c.get('/usuarios/2',headers=h['other']).status_code == 403
    assert c.get('/pedidos/usuario/2',headers=h['other']).status_code == 403
    assert c.post('/pedidos',headers=h['other'],json={'usuario_id':2,'itens':[{'produto_id':1,'quantidade':1}]}).status_code == 403
    assert c.post('/admin/query',headers=h['owner'],json={'sql':'SELECT 1'}).status_code == 403
    assert c.get('/usuarios/2',headers=h['owner']).status_code == 200
    assert c.get('/usuarios/2',headers={'Authorization':'Bearer invalid'}).status_code == 401
    with sqlite3.connect(path) as db:
        db.execute("UPDATE usuarios SET tipo='cliente' WHERE id=1")
    assert c.get('/usuarios',headers=h['admin']).status_code == 403
    with sqlite3.connect(path) as db:
        db.execute('DELETE FROM usuarios WHERE id=2')
    assert c.get('/usuarios/2',headers=h['owner']).status_code == 401


def test_sensitive_fields_are_not_serialized(shop):
    _,c,_,h=shop
    assert 'senha' not in c.get('/usuarios',headers=h['admin']).get_json()['dados'][0]
    assert 'senha' not in c.get('/usuarios/2',headers=h['owner']).get_json()['dados']
    health=c.get('/health').get_json()
    assert 'secret_key' not in health
    assert health['debug'] is False


def test_sql_data_cannot_bypass_login_or_break_unicode_writes(shop):
    _,c,path,h=shop
    assert c.post('/login',json={'email':"' OR 1=1 --",'senha':'wrong'}).status_code == 401
    response=c.post('/usuarios',json={'nome':"D'Ávila 東京",'email':"d'avila@example.test",'senha':"p'ass 東京"})
    assert response.status_code == 201
    assert c.post('/login',json={'email':"d'avila@example.test",'senha':"p'ass 東京"}).status_code == 200
    product=c.post('/produtos',headers=h['admin'],json={'nome':"Livro d'Ávila",'descricao':"D'água 東京",'preco':2.5,'estoque':3})
    assert product.status_code == 201
    assert c.get('/produtos/busca',query_string={'q':"d'Ávila"}).get_json()['total'] == 1
    assert c.get('/produtos/busca',query_string={'q':"' OR 1=1 --"}).get_json()['total'] == 0


def test_password_upgrade_and_modern_failure_no_fallback(shop):
    _,c,path,h=shop
    stored=rows(path,'SELECT senha FROM usuarios WHERE id=2')[0][0]
    assert stored != 'senhâ-東京'
    assert check_password_hash(stored,'senhâ-東京')
    c.post('/usuarios',json={'nome':'Novo','email':'new@example.test','senha':'password'})
    new=rows(path,"SELECT senha FROM usuarios WHERE email='new@example.test'")[0][0]
    assert check_password_hash(new,'password')
    assert c.post('/login',json={'email':'new@example.test','senha':new}).status_code == 401


@pytest.mark.parametrize('quantity',[0,-1,1.5,True,'1',None])
def test_order_rejects_invalid_quantity_without_effects(shop,quantity):
    _,c,path,h=shop
    response=c.post('/pedidos',headers=h['owner'],json={'usuario_id':2,'itens':[{'produto_id':1,'quantidade':quantity}]})
    assert response.status_code == 400
    assert rows(path,'SELECT COUNT(*) FROM pedidos') == [(0,)]
    assert rows(path,'SELECT estoque FROM produtos WHERE id=1') == [(10,)]


def test_cumulative_stock_and_unknown_user_rejected(shop):
    _,c,path,h=shop
    for payload in [
        {'usuario_id':2,'itens':[{'produto_id':1,'quantidade':6},{'produto_id':1,'quantidade':6}]},
        {'usuario_id':999,'itens':[{'produto_id':1,'quantidade':1}]}]:
        assert c.post('/pedidos',headers=h['admin'],json=payload).status_code == 400
    assert rows(path,'SELECT COUNT(*) FROM pedidos') == [(0,)]
    assert rows(path,'SELECT estoque FROM produtos WHERE id=1') == [(10,)]


@pytest.mark.parametrize('value',[True,float('nan'),float('inf'),None,'2',-1])
def test_prices_are_finite_numbers_not_bool(shop,value):
    _,c,path,h=shop
    response=c.post('/produtos',headers=h['admin'],json={'nome':'Produto','preco':value,'estoque':2})
    assert response.status_code == 400
    assert rows(path,'SELECT COUNT(*) FROM produtos') == [(2,)]


@pytest.mark.parametrize('body',[[],[1],None,{'nome':None,'preco':2,'estoque':1},
                                 {'nome':'A','preco':2,'estoque':1},
                                 {'nome':'Nome','preco':2,'estoque':1,'categoria':'invalid'}])
def test_update_validation_matches_creation(shop,body):
    _,c,path,h=shop
    assert c.put('/produtos/1',headers=h['admin'],json=body).status_code == 400
    assert rows(path,'SELECT nome FROM produtos WHERE id=1') == [('Café 東京',)]


def test_malformed_json_and_numeric_search_are_client_errors(shop):
    _,c,_,h=shop
    assert c.post('/produtos',headers=h['admin'],data='{',content_type='application/json').status_code == 400
    assert c.get('/produtos/busca?preco_min=nope').status_code == 400
    assert c.get('/produtos/busca?preco_max=inf').status_code == 400
    error=c.post('/admin/query',headers=h['admin'],json={'sql':'SELECT missing_private_column FROM usuarios'})
    assert error.status_code == 500
    assert 'missing_private_column' not in error.get_data(as_text=True)


def test_factory_lifecycle_does_not_seed_and_closes_connections(tmp_path):
    import app as module
    assert hasattr(module,'create_app'), 'factory missing: original global app mutates database lifecycle'
    path=tmp_path/'new.sqlite'
    app=module.create_app({'TESTING':True,'SECRET_KEY':'disposable-test-secret','DATABASE':str(path)})
    assert not path.exists()
    assert app.test_cli_runner().invoke(args=['init-db']).exit_code == 0
    from database import get_db
    with app.app_context():
        first=get_db()
        assert first.execute('SELECT COUNT(*) FROM usuarios').fetchone()[0] == 0
    with pytest.raises(sqlite3.ProgrammingError):
        first.execute('SELECT 1')
    with app.app_context():
        assert get_db() is not first
    assert app.test_cli_runner().invoke(args=['init-db']).exit_code == 0
    assert rows(path,'SELECT COUNT(*) FROM usuarios') == [(0,)]
    with pytest.raises(RuntimeError):
        module.create_app({'SECRET_KEY':'','DATABASE':str(path)})


def test_checkout_failure_rolls_back_all_writes_before_next_request(shop):
    _,c,path,h=shop
    with sqlite3.connect(path) as db:
        db.execute("CREATE TRIGGER fail_second BEFORE INSERT ON itens_pedido WHEN NEW.produto_id=2 BEGIN SELECT RAISE(ABORT,'private sentinel'); END")
    response=c.post('/pedidos',headers=h['owner'],json={'usuario_id':2,'itens':[{'produto_id':1,'quantidade':1},{'produto_id':2,'quantidade':1}]})
    assert response.status_code == 500
    c.post('/produtos',headers=h['admin'],json={'nome':'Other','preco':1,'estoque':1})
    assert rows(path,'SELECT COUNT(*) FROM pedidos') == [(0,)]
    assert rows(path,'SELECT COUNT(*) FROM itens_pedido') == [(0,)]
    assert rows(path,'SELECT estoque FROM produtos WHERE id=1') == [(10,)]


def test_concurrent_checkout_never_oversells(shop):
    app,_,path,h=shop
    def order(_):
        with app.test_client() as client:
            return client.post('/pedidos',headers=h['owner'],json={'usuario_id':2,'itens':[{'produto_id':1,'quantidade':7}]}).status_code
    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(order,range(2))) == [201,400]
    assert rows(path,'SELECT estoque FROM produtos WHERE id=1') == [(3,)]
    assert rows(path,'SELECT COUNT(*) FROM pedidos') == [(1,)]


def test_legacy_cutoff_and_token_expiry_use_controlled_clock(shop):
    app,c,path,h=shop
    assert 'CLOCK' in app.config, 'controlled authentication clock missing'
    app.config['CLOCK']=lambda: datetime(2030,1,1,tzinfo=timezone.utc)
    app.config['LEGACY_PASSWORD_CUTOFF']='2029-12-31T23:59:59+00:00'
    with sqlite3.connect(path) as db:
        db.execute("INSERT INTO usuarios(nome,email,senha,tipo) VALUES('Legacy','legacy@example.test','clear-password','cliente')")
    assert c.post('/login',json={'email':'legacy@example.test','senha':'clear-password'}).status_code == 401
    app.config['LEGACY_PASSWORD_CUTOFF']='2030-01-01T00:00:01+00:00'
    token=c.post('/login',json={'email':'legacy@example.test','senha':'clear-password'}).get_json()['token']
    app.config['CLOCK']=lambda: datetime(2031,1,1,tzinfo=timezone.utc)
    assert c.get('/usuarios/4',headers={'Authorization':'Bearer '+token}).status_code == 401
