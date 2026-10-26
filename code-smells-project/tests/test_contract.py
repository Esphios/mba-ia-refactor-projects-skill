"""Semantic baseline: literals independently derived from the original source."""
from conftest import rows

PRODUCT_KEYS = {'id','nome','descricao','preco','estoque','categoria','ativo','criado_em'}


def test_all_nineteen_contracts(shop):
    app, c, path, h = shop
    seen = set()
    def call(method, url, status=200, **kwargs):
        response = c.open(url, method=method, **kwargs)
        assert response.status_code == status, (method, url, response.get_json())
        assert response.is_json
        seen.add((method, url))
        return response.get_json()

    root = call('GET', '/')
    assert root['versao'] == '1.0.0'
    assert root['endpoints']['produtos'] == '/produtos'
    products = call('GET', '/produtos')['dados']
    assert [p['id'] for p in products] == [1, 2]
    assert set(products[0]) == PRODUCT_KEYS
    assert products[0]['nome'] == 'Café 東京'
    product = call('GET', '/produtos/1')['dados']
    assert product == products[0]
    found = call('GET', '/produtos/busca?q=caf%25&categoria=livros&preco_min=0&preco_max=13')
    assert found['total'] == 1 and found['dados'] == [product]
    created = call('POST', '/produtos', 201, headers=h['admin'], json={'nome':'Livro','preco':3,'estoque':4})
    new_id = created['dados']['id']
    default = c.get(f'/produtos/{new_id}').get_json()['dados']
    assert default['descricao'] == '' and default['categoria'] == 'geral' and default['ativo'] == 1
    call('PUT', f'/produtos/{new_id}', headers=h['admin'], json={'nome':'Livro novo','preco':4,'estoque':5})
    assert rows(path, 'SELECT nome,preco,estoque FROM produtos WHERE id=?', (new_id,)) == [('Livro novo',4.0,5)]
    call('DELETE', f'/produtos/{new_id}', headers=h['admin'])
    assert not rows(path,'SELECT id FROM produtos WHERE id=?',(new_id,))
    assert len(call('GET','/usuarios',headers=h['admin'])['dados']) == 3
    user = call('GET','/usuarios/2',headers=h['owner'])['dados']
    assert user['nome'] == 'João' and user['tipo'] == 'cliente'
    new = call('POST','/usuarios',201,json={'nome':'Novo','email':'new@example.test','senha':'secret'})
    assert rows(path,'SELECT tipo FROM usuarios WHERE id=?',(new['dados']['id'],)) == [('cliente',)]
    logged = call('POST','/login',json={'email':'joao@example.test','senha':'senhâ-東京'})
    assert logged['dados'] == {'id':2,'nome':'João','email':'joao@example.test','tipo':'cliente'}
    order = call('POST','/pedidos',201,headers=h['owner'],json={'usuario_id':2,'itens':[{'produto_id':1,'quantidade':2},{'produto_id':2,'quantidade':1}]})['dados']
    assert order['total'] == 32.25
    assert rows(path,'SELECT estoque FROM produtos ORDER BY id') == [(8,),(19,)]
    all_orders = call('GET','/pedidos',headers=h['admin'])['dados']
    own_orders = call('GET','/pedidos/usuario/2',headers=h['owner'])['dados']
    assert all_orders == own_orders
    assert set(all_orders[0]) == {'id','usuario_id','status','total','criado_em','itens'}
    assert all_orders[0]['itens'] == [
        {'produto_id':1,'produto_nome':'Café 東京','quantidade':2,'preco_unitario':12.5},
        {'produto_id':2,'produto_nome':'Mouse','quantidade':1,'preco_unitario':7.25}]
    call('PUT',f"/pedidos/{order['pedido_id']}/status",headers=h['admin'],json={'status':'cancelado'})
    assert rows(path,'SELECT estoque FROM produtos ORDER BY id') == [(8,),(19,)]
    report = call('GET','/relatorios/vendas',headers=h['admin'])['dados']
    assert report == {'total_pedidos':1,'faturamento_bruto':32.25,'desconto_aplicavel':0,
                      'faturamento_liquido':32.25,'pedidos_pendentes':0,'pedidos_aprovados':0,
                      'pedidos_cancelados':1,'ticket_medio':32.25}
    health = call('GET','/health')
    assert health['counts'] == {'produtos':2,'usuarios':4,'pedidos':1}
    assert health['status'] == 'ok' and health['database'] == 'connected'
    query = call('POST','/admin/query',headers=h['admin'],json={'sql':'SELECT nome FROM produtos ORDER BY id'})
    assert query['dados'] == [{'nome':'Café 東京'},{'nome':'Mouse'}]
    call('POST','/admin/query',headers=h['admin'],json={'sql':"UPDATE produtos SET estoque=9 WHERE id=1"})
    assert rows(path,'SELECT estoque FROM produtos WHERE id=1') == [(9,)]
    call('POST','/admin/reset-db',headers=h['admin'])
    assert [rows(path,'SELECT COUNT(*) FROM '+t)[0][0] for t in ('produtos','usuarios','pedidos','itens_pedido')] == [0,0,0,0]
    assert len(seen) == 19


def test_empty_missing_and_unknown_related_product(shop):
    _, c, path, h = shop
    assert c.get('/produtos/999').status_code == 404
    assert c.get('/usuarios/999',headers=h['admin']).status_code == 404
    assert c.get('/pedidos/usuario/3',headers=h['other']).get_json()['dados'] == []
    assert c.put('/pedidos/999/status',headers=h['admin'],json={'status':'aprovado'}).status_code == 200
    empty = c.get('/relatorios/vendas',headers=h['admin']).get_json()['dados']
    assert empty == {'total_pedidos':0,'faturamento_bruto':0,'desconto_aplicavel':0,'faturamento_liquido':0,
                     'pedidos_pendentes':0,'pedidos_aprovados':0,'pedidos_cancelados':0,'ticket_medio':0}
    order = c.post('/pedidos',headers=h['owner'],json={'usuario_id':2,'itens':[{'produto_id':1,'quantidade':1}]}).get_json()['dados']
    c.delete('/produtos/1',headers=h['admin'])
    result = c.get('/pedidos',headers=h['admin']).get_json()['dados']
    assert result[0]['id'] == order['pedido_id']
    assert result[0]['itens'][0]['produto_nome'] == 'Desconhecido'
    assert c.get('/not-a-route').status_code == 404
    assert c.patch('/produtos').status_code == 405
