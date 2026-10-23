from flask import g
from auth import authenticate, owner
from models import Task, User, Category
from models import repository as repo
from utils.validation import body, task_fields
from utils.serialization import task_data
from utils.dates import utc_naive
from errors import APIError

def visible_tasks(args,search=None):
    user=g.identity
    result=repo.tasks(None if user.is_admin() else user.id,search=search)
    for field in ('priority','user_id','category_id'):
        if args.get(field):
            try: value=int(args[field])
            except (ValueError,TypeError): raise APIError('Filtro inválido')
            result=[t for t in result if getattr(t,field)==value]
    if args.get('status'): result=[t for t in result if t.status==args['status']]
    return result

def listing(args,search=False):
    authenticate();result=visible_tasks(args,search=args.get('q','') if search else None)
    return [task_data(t,'base' if search else 'list') for t in result]

def detail(task_id):
    authenticate();task=repo.get(Task,task_id);owner(task.user_id)
    return task_data(task,'detail')

def write(data,task_id=None):
    authenticate();data=body(data)
    task=repo.get(Task,task_id) if task_id else Task()
    if task_id: owner(task.user_id)
    values=task_fields(data,not task_id)
    if not task_id and 'user_id' not in values: values['user_id']=g.identity.id
    if 'user_id' in values:
        owner(values['user_id'])
        if values['user_id'] is not None: repo.get(User,values['user_id'])
    if values.get('category_id') is not None: repo.get(Category,values['category_id'])
    for key,value in values.items(): setattr(task,key,value)
    if task_id: task.updated_at=utc_naive()
    repo.save(task)
    return task_data(task)

def remove(task_id):
    authenticate();task=repo.get(Task,task_id);owner(task.user_id);repo.delete(task)
    return {'message':'Task deletada com sucesso'}

def statistics(tasks):
    total=len(tasks);counts={s:sum(t.status==s for t in tasks) for s in ('pending','in_progress','done','cancelled')}
    return dict(total=total,**counts,overdue=sum(t.is_overdue() for t in tasks),completion_rate=round(counts['done']/total*100,2) if total else 0)

def stats():
    authenticate();return statistics(visible_tasks({}))
