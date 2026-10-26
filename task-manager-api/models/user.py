from database import db
from utils.domain import utcnow
import hashlib
import hmac
import re
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='user')
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at)
        }

    def set_password(self, pwd):

        self.password = generate_password_hash(pwd, method='scrypt')

    def check_password(self, pwd):
        if re.fullmatch(r'[a-fA-F0-9]{32}', self.password):
            return hmac.compare_digest(self.password.lower(), hashlib.md5(pwd.encode()).hexdigest())
        try:
            return check_password_hash(self.password, pwd)
        except (ValueError, TypeError):
            return False

    def is_admin(self):
        if self.role == 'admin':
            return True
        else:
            return False
