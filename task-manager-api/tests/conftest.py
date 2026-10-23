import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pytest
from app import create_app
from database import db
from models import User, Task, Category

@pytest.fixture
def app(tmp_path):
    app=create_app(dict(TESTING=True,SECRET_KEY='test-only-key',SQLALCHEMY_DATABASE_URI='sqlite:///'+str(tmp_path/'test.db'),LEGACY_MD5_CUTOFF='2099-01-01T00:00:00+00:00'))
    with app.app_context():
        db.create_all()
        for name,role in [('Admin','admin'),('Owner','user'),('Other','user')]:
            user=User(name=name,email=name.lower()+'@example.com',role=role);user.set_password('password');db.session.add(user)
        db.session.add(Category(name='Work'));db.session.commit()
        db.session.add(Task(title='Original task',user_id=2,category_id=1));db.session.commit()
    yield app
    with app.app_context(): db.session.remove();db.engine.dispose()

@pytest.fixture
def client(app): return app.test_client()

@pytest.fixture
def tokens(client):
    return {name:{'Authorization':'Bearer '+client.post('/login',json=dict(email=name+'@example.com',password='password')).json['token']} for name in ('admin','owner','other')}
