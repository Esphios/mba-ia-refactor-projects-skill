"""Persistence boundary. Controllers receive entities and aggregates, not ORM queries."""
from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import joinedload
from database import db
from models.user import User
from models.task import Task
from models.category import Category
from utils.domain import STATUSES, utcnow


def get(model, identifier):
    return db.session.get(model, identifier)


def email_user(email):
    return db.session.scalar(select(User).where(User.email == email))


def save(entity=None):
    if entity is not None:
        db.session.add(entity)
    db.session.commit()


def delete(entity):
    db.session.delete(entity)
    db.session.commit()


def delete_user(user):
    for task in tasks(user_id=user.id):
        db.session.delete(task)
    db.session.delete(user)
    db.session.commit()


def users():
    counts = select(Task.user_id, func.count(Task.id).label('total')).group_by(Task.user_id).subquery()
    return db.session.execute(select(User, func.coalesce(counts.c.total, 0)).outerjoin(counts, User.id == counts.c.user_id)).all()


def tasks(user_id=None, filters=None, related=False):
    statement = select(Task)
    if user_id is not None:
        statement = statement.where(Task.user_id == user_id)
    if related:
        statement = statement.options(joinedload(Task.user), joinedload(Task.category))
    filters = filters or {}
    if filters.get('q'):
        statement = statement.where(or_(Task.title.like('%' + filters['q'] + '%'), Task.description.like('%' + filters['q'] + '%')))
    for key in ('status', 'priority', 'user_id'):
        if filters.get(key) not in (None, ''):
            statement = statement.where(getattr(Task, key) == filters[key])
    return list(db.session.scalars(statement))


def categories():
    counts = select(Task.category_id, func.count(Task.id).label('total')).group_by(Task.category_id).subquery()
    return db.session.execute(select(Category, func.coalesce(counts.c.total, 0)).outerjoin(counts, Category.id == counts.c.category_id)).all()


def stats(user_id=None):
    unfinished = or_(Task.status.is_(None), Task.status.not_in(('done', 'cancelled')))
    statement = select(func.count(Task.id), *[func.coalesce(func.sum(case((Task.status == status, 1), else_=0)), 0) for status in STATUSES],
        func.coalesce(func.sum(case(((Task.due_date < utcnow()) & unfinished, 1), else_=0)), 0))
    if user_id is not None:
        statement = statement.where(Task.user_id == user_id)
    values = db.session.execute(statement).one()
    return dict(zip(('total', *STATUSES, 'overdue'), values))


def productivity():
    statement = select(User.id, User.name, func.count(Task.id),
        func.coalesce(func.sum(case((Task.status == 'done', 1), else_=0)), 0)).outerjoin(Task).group_by(User.id)
    return db.session.execute(statement).all()


def count(model):
    return db.session.scalar(select(func.count()).select_from(model))


def priority_counts():
    return dict(db.session.execute(select(Task.priority, func.count()).group_by(Task.priority)).all())


def overdue_tasks(now):
    unfinished = or_(Task.status.is_(None), Task.status.not_in(('done', 'cancelled')))
    return list(db.session.scalars(select(Task).where(Task.due_date < now, unfinished)))


def recent_counts(since):
    return (db.session.scalar(select(func.count()).select_from(Task).where(Task.created_at >= since)),
        db.session.scalar(select(func.count()).select_from(Task).where(Task.status == 'done', Task.updated_at >= since)))
