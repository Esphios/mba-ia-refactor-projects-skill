from datetime import timedelta
from auth import authenticate, admin, owner
from models import User
from models import repository as repo
from controllers.task_controller import statistics
from utils.constants import PRIORITIES, HIGH_PRIORITY_MAX
from utils.dates import utc_naive

def summary():
    admin();tasks=repo.tasks();users=repo.users();categories=repo.categories();now=utc_naive();recent=now-timedelta(days=7)
    stats=statistics(tasks)
    return dict(generated_at=str(now),overview=dict(total_tasks=len(tasks),total_users=len(users),total_categories=len(categories)),
        tasks_by_status={s:stats[s] for s in ('pending','in_progress','done','cancelled')},
        tasks_by_priority={label:sum(t.priority==priority for t in tasks) for priority,label in PRIORITIES.items()},
        overdue=dict(count=stats['overdue'],tasks=[dict(id=t.id,title=t.title,due_date=str(t.due_date),days_overdue=(now-utc_naive(t.due_date)).days) for t in tasks if t.is_overdue()]),
        recent_activity=dict(tasks_created_last_7_days=sum(utc_naive(t.created_at)>=recent for t in tasks),tasks_completed_last_7_days=sum(t.status=='done' and utc_naive(t.updated_at)>=recent for t in tasks)),
        user_productivity=[dict(user_id=u.id,user_name=u.name,total_tasks=len(u.tasks),completed_tasks=sum(t.status=='done' for t in u.tasks),completion_rate=statistics(u.tasks)['completion_rate']) for u in users])

def user_report(user_id):
    authenticate();owner(user_id);user=repo.get(User,user_id);tasks=repo.tasks(user_id);stats=statistics(tasks)
    stats['total_tasks']=stats.pop('total');stats['high_priority']=sum(t.priority<=HIGH_PRIORITY_MAX for t in tasks)
    return dict(user=dict(id=user.id,name=user.name,email=user.email),statistics=stats)
