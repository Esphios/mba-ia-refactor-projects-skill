"""Boot a real child process against disposable fixtures and exercise all 22 pairs."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import socket
import urllib.request
import urllib.error
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import create_app
from database import db
from models import User, Task, Category

def main():
    root=Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix='task-manager-http-') as temp:
        database=Path(temp)/'http.db'
        config=dict(SECRET_KEY='disposable-http-test-key',SQLALCHEMY_DATABASE_URI='sqlite:///'+str(database))
        app=create_app(config)
        with app.app_context():
            db.create_all()
            for name,role in [('admin','admin'),('owner','user')]:
                u=User(name=name,email=name+'@example.com',role=role);u.set_password('password');db.session.add(u)
            db.session.add(Category(name='Fixture'));db.session.commit()
            db.session.add(Task(title='HTTP fixture',user_id=2,category_id=1));db.session.commit();db.session.remove();db.engine.dispose()
        with socket.socket() as sock:
            sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
        env=os.environ.copy();env.update(SECRET_KEY=config['SECRET_KEY'],DATABASE_URL=config['SQLALCHEMY_DATABASE_URI'],PORT=str(port),SMTP_ENABLED='false',PYTHONUNBUFFERED='1')
        log=Path(temp)/'boot.log'
        with log.open('w+',encoding='utf-8') as output:
            process=subprocess.Popen([sys.executable,'app.py'],cwd=root,env=env,stdout=output,stderr=subprocess.STDOUT)
            def http(method,path,payload=None,token=None):
                headers={'Content-Type':'application/json'}
                if token: headers['Authorization']='Bearer '+token
                request=urllib.request.Request(f'http://127.0.0.1:{port}'+path,data=json.dumps(payload).encode() if payload is not None else None,headers=headers,method=method)
                try:
                    with urllib.request.urlopen(request,timeout=10) as response: return response.status,json.load(response)
                except urllib.error.HTTPError as error: return error.code,json.load(error)
            try:
                for attempt in range(100):
                    try:
                        if http('GET','/health')[0]==200: break
                    except (OSError,TimeoutError): pass
                    if process.poll() is not None: raise RuntimeError('Server exited before readiness')
                    time.sleep(.1)
                else: raise RuntimeError('Server readiness timeout')
                tokens={name:http('POST','/login',dict(email=name+'@example.com',password='password'))[1]['token'] for name in ('admin','owner')}
                cases=[('GET','/',None,None,200),('GET','/health',None,None,200),('GET','/tasks',None,'owner',200),('GET','/tasks/1',None,'owner',200),('POST','/tasks',{'title':'HTTP created','user_id':2},'owner',201),('PUT','/tasks/1',{'title':'HTTP updated'},'owner',200),('GET','/tasks/search?q=HTTP',None,'owner',200),('GET','/tasks/stats',None,'owner',200),('GET','/users',None,'admin',200),('GET','/users/2',None,'owner',200),('POST','/users',dict(name='New',email='new@example.com',password='password'),None,201),('PUT','/users/2',{'name':'HTTP owner'},'owner',200),('GET','/users/2/tasks',None,'owner',200),('POST','/login',dict(email='owner@example.com',password='password'),None,200),('GET','/reports/summary',None,'admin',200),('GET','/reports/user/2',None,'owner',200),('GET','/categories',None,'owner',200),('POST','/categories',{'name':'HTTP category'},'admin',201),('PUT','/categories/2',{'name':'Updated category'},'admin',200),('DELETE','/categories/2',None,'admin',200),('DELETE','/tasks/1',None,'owner',200),('DELETE','/users/3',None,'admin',200)]
                for method,path,payload,identity,expected in cases:
                    status,result=http(method,path,payload,tokens.get(identity))
                    assert status==expected,(method,path,status,result)
                    assert 'password' not in json.dumps(result) and 'scrypt:' not in json.dumps(result)
                    print(f'{method} {path}: expected={expected} observed={status} PASS')
                assert http('GET','/tasks')[0]==401
                assert http('GET','/users',token=tokens['owner'])[0]==403
                print('Negative real HTTP: anonymous 401 and ordinary-user admin denial 403 PASS')
                print('HTTP_MATRIX 22/22 PASS')
            finally:
                if os.name=='nt':
                    # Windows virtualenv executables may launch an interpreter child.
                    # Stop the owned tree so file handles close before temp cleanup.
                    subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False)
                else:
                    process.terminate()
                try: process.wait(timeout=10)
                except subprocess.TimeoutExpired: process.kill();process.wait()
                output.flush();output.seek(0)
                print('REAL_PROCESS_BOOT_LOG')
                print(output.read())
if __name__=='__main__': main()
