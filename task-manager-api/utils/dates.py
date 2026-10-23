from datetime import datetime, timezone

def utc_naive(value=None):
    value = value or datetime.now(timezone.utc)
    return value.astimezone(timezone.utc).replace(tzinfo=None) if value.tzinfo else value

def format_date(value):
    return str(utc_naive(value)) if value is not None else None

def overdue(task, now=None):
    return bool(task.due_date and utc_naive(task.due_date) < utc_naive(now) and task.status not in ('done','cancelled'))
