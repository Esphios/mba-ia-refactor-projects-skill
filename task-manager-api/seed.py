"""Opt-in fixtures for an empty disposable database; never clears existing data."""
import os
from app import create_app
from database import db
from models import User, Task, Category

def seed_data():
    app=create_app()
    with app.app_context():
        db.create_all()
        if any(db.session.scalar(db.select(model.id).limit(1)) is not None for model in (User,Task,Category)):
            raise SystemExit('Seed recusado: banco não vazio')
        password=os.environ.get('SEED_ADMIN_PASSWORD','')
        if len(password)<4: raise SystemExit('Configure SEED_ADMIN_PASSWORD com pelo menos 4 caracteres')
        user=User(name='Demo Admin',email='admin@example.com',role='admin')
        user.set_password(password)
        category=Category(name='Demo',description='Disposable example')
        try:
            db.session.add_all([user,category]);db.session.flush()
            db.session.add(Task(title='Example task',user_id=user.id,category_id=category.id))
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        print('Fixtures criadas em banco vazio')

if __name__=='__main__': seed_data()
