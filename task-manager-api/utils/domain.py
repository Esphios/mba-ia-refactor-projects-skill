"""Shared domain values; dates retain the legacy naive-UTC storage contract."""
from datetime import datetime, timezone

STATUSES = ('pending', 'in_progress', 'done', 'cancelled')
ROLES = ('user', 'admin', 'manager')
MIN_TITLE = 3
MAX_TITLE = 200
MIN_PASSWORD = 4
MIN_PRIORITY = 1
MAX_PRIORITY = 5
DEFAULT_PRIORITY = 3
DEFAULT_COLOR = '#000000'


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def overdue(task, now=None):
    return bool(task.due_date and task.due_date < (now or utcnow()) and task.status not in ('done', 'cancelled'))


def percentage(part, total):
    return round(part / total * 100, 2) if total else 0
