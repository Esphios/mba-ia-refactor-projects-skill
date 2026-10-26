"""Contract probes from regression-checks; independent literal expectations."""
import sqlite3
from datetime import datetime, timezone

import pytest
from conftest import rows
from werkzeug.security import generate_password_hash


@pytest.mark.parametrize('url,body,message',[
    ('/login',{},'Email e senha são obrigatórios'),
    ('/admin/query',{},'Query não informada'),
    ('/pedidos/999/status',{},'Status inválido')])
def test_empty_objects_keep_known_error_messages(shop,url,body,message):
    _,c,_,h=shop
    method='PUT' if '/status' in url else 'POST'
    response=c.open(url,method=method,json=body,headers=h['admin'])
    assert response.status_code == 400
    assert response.get_json() == {'erro':message}


def test_health_failure_retains_envelope_without_internal_details(shop):
    _,c,path,_=shop
    with sqlite3.connect(path) as db:
        db.execute('DROP TABLE produtos')
    response=c.get('/health')
    assert response.status_code == 500
    assert response.get_json() == {'status':'erro','detalhes':'Erro interno do servidor'}


@pytest.mark.parametrize('stage,trigger',[
    ('order',"CREATE TRIGGER fail BEFORE INSERT ON pedidos BEGIN SELECT RAISE(ABORT,'private'); END"),
    ('item',"CREATE TRIGGER fail BEFORE INSERT ON itens_pedido BEGIN SELECT RAISE(ABORT,'private'); END"),
    ('stock',"CREATE TRIGGER fail BEFORE UPDATE ON produtos BEGIN SELECT RAISE(ABORT,'private'); END")])
def test_each_checkout_write_failure_is_atomic(shop,stage,trigger):
    _,c,path,h=shop
    with sqlite3.connect(path) as db:
        db.execute(trigger)
    assert c.post('/pedidos',headers=h['owner'],json={'usuario_id':2,'itens':[{'produto_id':1,'quantidade':2}]}).status_code == 500
    assert rows(path,'SELECT COUNT(*) FROM pedidos') == [(0,)]
    assert rows(path,'SELECT COUNT(*) FROM itens_pedido') == [(0,)]
    assert rows(path,'SELECT estoque FROM produtos ORDER BY id') == [(10,),(20,)]


def test_list_select_count_is_constant_with_one_and_twenty_orders(shop):
    app,c,path,h=shop
    from database import get_db
    from models.orders import Orders
    counts=[]
    for n in (1,20):
        with sqlite3.connect(path) as db:
            db.execute('DELETE FROM itens_pedido'); db.execute('DELETE FROM pedidos')
            for i in range(n):
                order=db.execute("INSERT INTO pedidos(usuario_id,status,total) VALUES(2,'pendente',12.5)").lastrowid
                db.execute('INSERT INTO itens_pedido(pedido_id,produto_id,quantidade,preco_unitario) VALUES(?,1,1,12.5)',(order,))
        with app.app_context():
            queries=[]
            get_db().set_trace_callback(lambda sql:queries.append(sql) if sql.lstrip().upper().startswith('SELECT') else None)
            result=Orders(get_db()).list(2)
            assert len(result) == n
            assert all(row['itens'][0]['produto_nome']=='Café 東京' for row in result)
            counts.append(len(queries))
    assert counts == [1,1]


def test_order_listing_is_a_consistent_single_query_during_concurrent_insert(shop):
    app,_,path,_=shop
    from database import get_db
    from models.orders import Orders
    with sqlite3.connect(path) as db:
        first=db.execute("INSERT INTO pedidos(usuario_id,status,total) VALUES(2,'pendente',12.5)").lastrowid
        db.execute('INSERT INTO itens_pedido(pedido_id,produto_id,quantidade,preco_unitario) VALUES(?,1,1,12.5)',(first,))
    with app.app_context():
        connection=get_db(); inserted=[]
        def insert_before_item_read(sql):
            if not inserted and 'itens_pedido' in sql:
                inserted.append(True)
                with sqlite3.connect(path) as other:
                    order=other.execute("INSERT INTO pedidos(usuario_id,status,total) VALUES(2,'pendente',7.25)").lastrowid
                    other.execute('INSERT INTO itens_pedido(pedido_id,produto_id,quantidade,preco_unitario) VALUES(?,2,1,7.25)',(order,))
        connection.set_trace_callback(insert_before_item_read)
        result=Orders(connection).list()
        assert [row['id'] for row in result] in ([first],[first,first+1])
        assert all(len(row['itens']) == 1 for row in result)
        assert rows(path,'SELECT COUNT(*) FROM pedidos') == [(2,)]


@pytest.mark.parametrize('total,discount',[(0,0),(999.99,0),(1000,0),(1000.01,20),
    (5000,100),(5000.01,250),(10000,500),(10000.01,1000)])
def test_discount_thresholds_keep_strict_comparison_and_rounding(shop,total,discount):
    _,c,path,h=shop
    with sqlite3.connect(path) as db:
        db.execute("INSERT INTO pedidos(usuario_id,status,total) VALUES(2,'cancelado',?)",(total,))
    report=c.get('/relatorios/vendas',headers=h['admin']).get_json()['dados']
    assert report['desconto_aplicavel'] == discount
    assert report['faturamento_bruto'] == total
    assert report['ticket_medio'] == total
    assert report['pedidos_cancelados'] == 1


def test_like_unicode_case_wildcards_and_zero_bounds(shop):
    _,c,_,_=shop
    for query,total in [({'q':'CAF%'},1),({'q':'Caf_'},1),({'q':'東京'},1),({'q':'AÇÃO'},0),
                        ({'q':'ação'},1),({'preco_max':'0'},2),({'preco_min':''},2),
                        ({'categoria':'missing'},0),({'q':'%'},2)]:
        response=c.get('/produtos/busca',query_string=query)
        assert response.status_code == 200
        assert response.get_json()['total'] == total


def test_distinct_salts_and_cutoff_exact_boundary(shop):
    app,c,path,_=shop
    for email in ('one@example.test','two@example.test'):
        assert c.post('/usuarios',json={'nome':'Novo','email':email,'senha':'same-password'}).status_code == 201
    hashes=rows(path,"SELECT senha FROM usuarios WHERE email IN ('one@example.test','two@example.test')")
    assert hashes[0][0] != hashes[1][0]
    with sqlite3.connect(path) as db:
        db.execute("INSERT INTO usuarios(nome,email,senha) VALUES('Legado','legacy@example.test','old-password')")
    app.config['CLOCK']=lambda:datetime(2030,1,1,tzinfo=timezone.utc)
    app.config['LEGACY_PASSWORD_CUTOFF']='2030-01-01T00:00:00+00:00'
    assert c.post('/login',json={'email':'legacy@example.test','senha':'old-password'}).status_code == 401


def test_duplicate_emails_authenticate_the_matching_account_and_upgrade_only_it(shop):
    _,c,path,_=shop
    with sqlite3.connect(path) as db:
        db.execute("INSERT INTO usuarios(nome,email,senha,tipo) VALUES('Primeira','dup@example.test',?,'cliente')",
            (generate_password_hash('first-password'),))
        second=db.execute("INSERT INTO usuarios(nome,email,senha,tipo) VALUES('Segunda','dup@example.test','second-password','cliente')").lastrowid
    response=c.post('/login',json={'email':'dup@example.test','senha':'second-password'})
    assert response.status_code == 200 and response.get_json()['dados']['id'] == second
    stored=rows(path,'SELECT id,senha FROM usuarios WHERE email=? ORDER BY id',('dup@example.test',))
    assert stored[0][1].startswith('scrypt:') and stored[1][1].startswith('scrypt:')
    assert c.post('/login',json={'email':'dup@example.test','senha':'wrong'}).status_code == 401


def test_large_sqlite_integers_preserve_original_endpoint_semantics(shop):
    _,c,path,h=shop
    huge=9223372036854775808
    assert c.get(f'/produtos/{huge}').status_code == 404
    status=c.put(f'/pedidos/{huge}/status',json={'status':'aprovado'},headers=h['admin'])
    assert status.status_code == 200
    created=c.post('/produtos',json={'nome':'Numeric','preco':huge,'estoque':1},headers=h['admin'])
    assert created.status_code == 201
    value=rows(path,'SELECT preco FROM produtos WHERE id=?',(created.get_json()['dados']['id'],))[0][0]
    assert value == float(huge)


def test_seed_is_explicit_empty_only_and_reset_survives_restart(shop):
    app,c,path,h=shop
    runner=app.test_cli_runner()
    assert runner.invoke(args=['seed-demo']).exit_code != 0
    assert runner.invoke(args=['seed-demo','--disposable']).exit_code != 0
    assert c.post('/admin/reset-db',headers=h['admin']).status_code == 200
    from app import create_app
    restarted=create_app(dict(app.config))
    assert restarted.test_client().get('/health').get_json()['counts'] == {'produtos':0,'usuarios':0,'pedidos':0}
    assert runner.invoke(args=['seed-demo','--disposable']).exit_code == 0
    assert rows(path,'SELECT COUNT(*) FROM produtos') == [(10,)]
    assert rows(path,'SELECT COUNT(*) FROM usuarios') == [(0,)]


def test_existing_null_product_name_differs_from_missing_relation(shop):
    _,c,path,h=shop
    assert c.post('/pedidos',headers=h['owner'],json={'usuario_id':2,'itens':[{'produto_id':1,'quantidade':1}]}).status_code == 201
    with sqlite3.connect(path) as db:
        db.execute('UPDATE produtos SET nome=NULL WHERE id=1')
        db.execute('ALTER TABLE pedidos ADD COLUMN private_note TEXT')
        db.execute("UPDATE pedidos SET private_note='private sentinel'")
    order=c.get('/pedidos',headers=h['admin']).get_json()['dados'][0]
    assert order['itens'][0]['produto_nome'] is None
    assert 'private_note' not in order
