import sys,tempfile,os,json,importlib.metadata
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from flask import Flask
from database import db
from routes.task_routes import task_bp
from routes.user_routes import user_bp
from routes.report_routes import report_bp
from models import User,Task,Category
app=Flask(__name__);app.config.update(SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',TESTING=True)
db.init_app(app)
for bp in (task_bp,user_bp,report_bp):app.register_blueprint(bp)
with app.app_context():
 db.create_all();u=User(name='Baseline',email='baseline@example.com');u.set_password('pass');db.session.add(u);db.session.commit()
 c=app.test_client(); print(json.dumps({'runtime':sys.version,'versions':{n:importlib.metadata.version(n) for n in ['Flask','Flask-SQLAlchemy','SQLAlchemy','Werkzeug','itsdangerous']},'registered_pairs':sum(len(r.methods-{'HEAD','OPTIONS'}) for r in app.url_map.iter_rules() if r.endpoint!='static'),'login_status':c.post('/login',json={'email':u.email,'password':'pass'}).status_code,'password_exposed':'password' in c.get('/users/1').json,'anonymous_users_status':c.get('/users').status_code,'task_create_status':c.post('/tasks',json={'title':'Baseline task','user_id':u.id}).status_code},indent=2))
