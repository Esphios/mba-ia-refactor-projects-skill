import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

def test_user_serializer_never_exposes_password():
    from models.user import User
    user=User(name='User',email='user@example.com',password='sentinel')
    assert 'password' not in user.to_dict()

def test_new_password_is_scrypt():
    from models.user import User
    user=User(); user.set_password('valid-password')
    assert user.password.startswith('scrypt:')

def test_factory_exists():
    from app import create_app
    assert callable(create_app)
