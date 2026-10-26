from datetime import timedelta
from models import store
from models.user import User
from models.category import Category
from controllers.user_controller import find as find_user
from services.security import own_user
from utils import validation
from utils.domain import DEFAULT_COLOR, STATUSES, overdue, percentage, utcnow
from utils.errors import ApiError


def summary_report():
    now = utcnow()
    stats = store.stats()
    priorities = store.priority_counts()
    late_tasks = store.overdue_tasks(now)
    recent_tasks, recent_done = store.recent_counts(now - timedelta(days=7))
    return {'generated_at': str(now),
        'overview': {'total_tasks': stats['total'], 'total_users': store.count(User), 'total_categories': store.count(Category)},
        'tasks_by_status': {key: stats[key] for key in STATUSES},
        'tasks_by_priority': {name: priorities.get(priority, 0) for priority, name in enumerate(('critical', 'high', 'medium', 'low', 'minimal'), 1)},
        'overdue': {'count': len(late_tasks), 'tasks': [{'id': task.id, 'title': task.title,
            'due_date': str(task.due_date), 'days_overdue': (now - task.due_date).days} for task in late_tasks]},
        'recent_activity': {'tasks_created_last_7_days': recent_tasks, 'tasks_completed_last_7_days': recent_done},
        'user_productivity': [{'user_id': identifier, 'user_name': name, 'total_tasks': total,
            'completed_tasks': done, 'completion_rate': percentage(done, total)}
            for identifier, name, total, done in store.productivity()]}, 200


def user_report(user_id):
    own_user(user_id)
    user = find_user(user_id)
    tasks = store.tasks(user_id=user_id)
    stats = {'total_tasks': len(tasks), **{status: sum(task.status == status for task in tasks) for status in STATUSES},
        'overdue': sum(overdue(task) for task in tasks), 'high_priority': sum(task.priority <= 2 for task in tasks)}
    stats['completion_rate'] = percentage(stats['done'], len(tasks))
    return {'user': {'id': user.id, 'name': user.name, 'email': user.email}, 'statistics': stats}, 200


def get_categories():
    return [{**category.to_dict(), 'task_count': count} for category, count in store.categories()], 200


def create_category(data):
    values = validation.category_data(data, create=True)
    category = Category(name=values['name'], description=values.get('description', ''), color=values.get('color', DEFAULT_COLOR))
    store.save(category)
    return category.to_dict(), 201


def find_category(cat_id):
    category = store.get(Category, cat_id)
    if category is None:
        raise ApiError('Categoria não encontrada', 404)
    return category


def update_category(cat_id, data):
    category = find_category(cat_id)
    values = validation.category_data(data)
    for key, value in values.items():
        setattr(category, key, value)
    store.save()
    return category.to_dict(), 200


def delete_category(cat_id):
    store.delete(find_category(cat_id))
    return {'message': 'Categoria deletada'}, 200
