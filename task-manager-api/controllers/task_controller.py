from models import store
from models.task import Task
from models.user import User
from models.category import Category
from services.security import identity, own_task, scope
from utils import validation
from utils.domain import DEFAULT_PRIORITY, overdue, percentage, utcnow
from utils.errors import ApiError


def find(task_id):
    task = store.get(Task, task_id)
    if task is None:
        raise ApiError('Task não encontrada', 404)
    own_task(task)
    return task


def list_tasks():
    result = []
    for task in store.tasks(user_id=scope(), related=True):
        item = task.to_dict()
        item.update(overdue=overdue(task), user_name=task.user.name if task.user else None,
            category_name=task.category.name if task.category else None)
        result.append(item)
    return result, 200


def get_task(task_id):
    task = find(task_id)
    return {**task.to_dict(), 'overdue': overdue(task)}, 200


def apply_task(data, task=None):
    create = task is None
    values = validation.task_data(data, create=create)
    actor = identity()
    if actor.role not in ('admin', 'manager'):
        if 'user_id' in values and values['user_id'] != actor.id:
            raise ApiError('Acesso negado', 403)
        if create:
            values['user_id'] = actor.id
    for key, model, message in [('user_id', User, 'Usuário não encontrado'), ('category_id', Category, 'Categoria não encontrada')]:
        if values.get(key) and store.get(model, values[key]) is None:
            raise ApiError(message, 404)
    if create:
        task = Task(description='', status='pending', priority=DEFAULT_PRIORITY)
    for key, value in values.items():
        setattr(task, key, value)
    if not create:
        task.updated_at = utcnow()
    store.save(task)
    return task.to_dict(), 201 if create else 200


def create_task(data):
    return apply_task(data)


def update_task(task_id, data):
    return apply_task(data, find(task_id))


def delete_task(task_id):
    store.delete(find(task_id))
    return {'message': 'Task deletada com sucesso'}, 200


def search_tasks(args):
    return [task.to_dict() for task in store.tasks(user_id=scope(), filters=validation.search_data(args))], 200


def task_stats():
    stats = store.stats(scope())
    stats['completion_rate'] = percentage(stats['done'], stats['total'])
    return stats, 200
