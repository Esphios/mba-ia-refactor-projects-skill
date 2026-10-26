"""One-command real HTTP validation; owns process, ephemeral port and disposable DB."""
import argparse
from contextlib import closing
import json
import os
import queue
import secrets
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def run():
    results=[]
    processes=[]
    covered=set()
    with tempfile.TemporaryDirectory(prefix='shop-http-') as directory:
        database=Path(directory)/'http.sqlite'
        password=secrets.token_urlsafe(24)
        secret=secrets.token_urlsafe(48)
        from app import create_app
        from werkzeug.security import generate_password_hash
        app=create_app({'DATABASE':str(database),'SECRET_KEY':secret})
        init=app.test_cli_runner().invoke(args=['init-db'])
        assert init.exit_code == 0
        with closing(sqlite3.connect(database)) as db, db:
            db.execute("INSERT INTO usuarios(id,nome,email,senha,tipo) VALUES(1,'Admin','admin@example.test',?,'admin')",(generate_password_hash(password),))
        environment=dict(os.environ,SHOP_DATABASE=str(database),SHOP_SECRET_KEY=secret,PYTHONUTF8='1')
        environment.pop('SHOP_DEBUG',None)
        environment.pop('SHOP_LEGACY_PASSWORD_CUTOFF',None)

        def start():
            log=open(Path(directory)/('server-'+str(len(processes))+'.log'),'w+',encoding='utf-8')
            process=subprocess.Popen([sys.executable,str(Path(__file__).with_name('http_server.py'))],
                cwd=ROOT,env=environment,stdout=subprocess.PIPE,stderr=log,text=True,encoding='utf-8',
                creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
            processes.append({'process':process,'log':log,'pid':process.pid})
            ready=queue.Queue()
            threading.Thread(target=lambda:ready.put(process.stdout.readline()),daemon=True).start()
            started=time.monotonic()
            try:
                line=ready.get(timeout=15)
            except queue.Empty as exc:
                raise AssertionError('Readiness timeout (15s)') from exc
            port=json.loads(line)['port']
            processes[-1].update(port=port,ready_seconds=round(time.monotonic()-started,3))
            return 'http://127.0.0.1:'+str(port)

        def stop(info):
            process=info['process']
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill(); process.wait(timeout=10)
            info['stopped']=process.poll() is not None
            process.stdout.close()
            info['log'].flush()
            info['log'].seek(0)
            log=info['log'].read()
            assert secret not in log and password not in log
            info['log'].close()

        try:
            base=start()
            def call(method,path,status=200,body=None,token=None,label=None):
                headers={}
                if body is not None:
                    headers['Content-Type']='application/json; charset=utf-8'
                if token:
                    headers['Authorization']='Bearer '+token
                data=None if body is None else json.dumps(body,ensure_ascii=False).encode('utf-8')
                request=Request(base+path,data=data,headers=headers,method=method)
                try:
                    response=urlopen(request,timeout=10)
                except HTTPError as error:
                    response=error
                with response:
                    actual=response.status
                    value=json.loads(response.read().decode('utf-8'))
                assert actual == status, (method,path,actual,status)
                # Never emit credential-bearing response bodies.
                results.append({'method':method,'path':path,'status':actual})
                if label:
                    covered.add((method,label))
                return value

            assert call('GET','/',label='/')['versao']=='1.0.0'
            admin=call('POST','/login',body={'email':'admin@example.test','senha':password},label='/login')['token']
            user=call('POST','/usuarios',201,body={'nome':"D'Ávila 東京",'email':"d'avila@example.test",'senha':password},label='/usuarios')['dados']['id']
            owner=call('POST','/login',body={'email':"d'avila@example.test",'senha':password})['token']
            product=call('POST','/produtos',201,body={'nome':"Livro d'Ávila",'descricao':'東京','preco':12.5,'estoque':10},token=admin,label='/produtos')['dados']['id']
            assert len(call('GET','/produtos',label='/produtos')['dados'])==1
            assert call('GET',f'/produtos/{product}',label='/produtos/<int:id>')['dados']['preco']==12.5
            assert call('GET','/produtos/busca?q=%25',label='/produtos/busca')['total']==1
            call('PUT',f'/produtos/{product}',body={'nome':"Livro d'Ávila",'preco':12.5,'estoque':10},token=admin,label='/produtos/<int:id>')
            users=call('GET','/usuarios',token=admin,label='/usuarios')['dados']
            assert len(users)==2 and all('senha' not in row for row in users)
            assert call('GET',f'/usuarios/{user}',token=owner,label='/usuarios/<int:id>')['dados']['nome']=="D'Ávila 東京"
            order=call('POST','/pedidos',201,body={'usuario_id':user,'itens':[{'produto_id':product,'quantidade':2}]},token=owner,label='/pedidos')['dados']
            assert order['total']==25
            assert len(call('GET','/pedidos',token=admin,label='/pedidos')['dados'])==1
            assert call('GET',f'/pedidos/usuario/{user}',token=owner,label='/pedidos/usuario/<int:usuario_id>')['dados'][0]['itens'][0]['quantidade']==2
            call('PUT',f"/pedidos/{order['pedido_id']}/status",body={'status':'cancelado'},token=admin,label='/pedidos/<int:pedido_id>/status')
            assert call('GET','/relatorios/vendas',token=admin,label='/relatorios/vendas')['dados']['faturamento_bruto']==25
            health=call('GET','/health',label='/health')
            assert health['counts']=={'produtos':1,'usuarios':2,'pedidos':1}
            assert 'secret_key' not in health and health['debug'] is False
            for method,path,body in [
                ('POST','/produtos',{'nome':'Test','preco':1,'estoque':1}),
                ('PUT',f'/produtos/{product}',{'nome':'Test','preco':1,'estoque':1}),
                ('DELETE',f'/produtos/{product}',None), ('GET','/usuarios',None),
                ('GET',f'/usuarios/{user}',None), ('GET','/pedidos',None),
                ('GET',f'/pedidos/usuario/{user}',None),
                ('POST','/pedidos',{'usuario_id':user,'itens':[{'produto_id':product,'quantidade':1}]}),
                ('PUT',f"/pedidos/{order['pedido_id']}/status",{'status':'aprovado'}),
                ('GET','/relatorios/vendas',None), ('POST','/admin/query',{'sql':'SELECT 1'}),
                ('POST','/admin/reset-db',None)]:
                call(method,path,401,body=body)
            call('POST','/admin/query',403,body={'sql':'SELECT 1'},token=owner)
            call('GET','/usuarios/1',403,token=owner)
            assert call('POST','/admin/query',body={'sql':'SELECT estoque FROM produtos'},token=admin,label='/admin/query')['dados']==[{'estoque':8}]
            call('POST','/admin/query',body={'sql':'CREATE TABLE admin_probe(value TEXT)'},token=admin)
            call('POST','/admin/query',body={'sql':"INSERT INTO admin_probe VALUES('東京')"},token=admin)
            assert call('POST','/admin/query',body={'sql':'SELECT * FROM admin_probe'},token=admin)['dados']==[{'value':'東京'}]
            call('DELETE',f'/produtos/{product}',token=admin,label='/produtos/<int:id>')
            assert call('GET','/pedidos',token=admin)['dados'][0]['itens'][0]['produto_nome']=='Desconhecido'
            call('POST','/admin/reset-db',token=admin,label='/admin/reset-db')
            assert call('GET','/health')['counts']=={'produtos':0,'usuarios':0,'pedidos':0}
            with closing(sqlite3.connect(database)) as db:
                assert db.execute('SELECT COUNT(*) FROM itens_pedido').fetchone()[0]==0
            stop(processes[-1])
            base=start()
            assert call('GET','/health')['counts']=={'produtos':0,'usuarios':0,'pedidos':0}
            assert len(covered)==19
        finally:
            for info in processes:
                if not info.get('stopped'):
                    stop(info)
        metadata=[{key:value for key,value in info.items() if key not in ('process','log')} for info in processes]
    assert not database.parent.exists()
    return {'result':'PASS','contracts':len(covered),'http_checks':len(results),'processes':metadata,
            'cleanup':'processes stopped and disposable directory removed','checks':results,
            'command':[Path(sys.executable).name,'tests/http_server.py'], 'readiness_timeout_seconds':15}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    result=run()
    serialized=json.dumps(result,ensure_ascii=False,indent=2)
    if args.output:
        args.output.write_text(serialized+'\n',encoding='utf-8')
    print(serialized)
