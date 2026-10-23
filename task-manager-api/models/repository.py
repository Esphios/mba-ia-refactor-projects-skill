from sqlalchemy.orm import joinedload, selectinload
from database import db
from models import Task, User, Category
from errors import APIError

def get(model, identity):
    record=db.session.get(model,identity)
    if record is None: raise APIError('Recurso não encontrado',404)
    return record

def tasks(user_id=None, search=None):
    query=db.select(Task).options(joinedload(Task.user),joinedload(Task.category)).order_by(Task.id)
    if user_id is not None: query=query.where(Task.user_id==user_id)
    if search:
        pattern=f'%{search}%'
        query=query.where(db.or_(Task.title.like(pattern),Task.description.like(pattern)))
    return list(db.session.scalars(query))

def users():
    return list(db.session.scalars(db.select(User).options(selectinload(User.tasks)).order_by(User.id)))

def categories():
    return list(db.session.scalars(db.select(Category).options(selectinload(Category.tasks)).order_by(Category.id)))

def email_user(email):
    return db.session.scalar(db.select(User).where(User.email==email))

def save(record):
    db.session.add(record); db.session.commit()
    return record

def delete(record):
    db.session.delete(record); db.session.commit()
