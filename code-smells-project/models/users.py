import serializers
from domain import sqlite_integer


class Users:
    def __init__(self, db):
        self.db = db

    def all(self):
        return [serializers.user(row) for row in self.db.execute('SELECT * FROM usuarios ORDER BY id')]

    def get(self, user_id):
        if not sqlite_integer(user_id):
            return None
        return self.db.execute('SELECT * FROM usuarios WHERE id=?', (user_id,)).fetchone()

    def by_email(self, email):
        return self.db.execute('SELECT * FROM usuarios WHERE email=? ORDER BY id', (email,)).fetchall()

    def create(self, name, email, password_hash):
        return self.db.execute('INSERT INTO usuarios(nome,email,senha,tipo) VALUES(?,?,?,?)',
            (name, email, password_hash, 'cliente')).lastrowid

    def upgrade_password(self, user_id, password_hash):
        self.db.execute('UPDATE usuarios SET senha=? WHERE id=?', (password_hash, user_id))
