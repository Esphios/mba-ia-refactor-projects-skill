from utils.dates import overdue

def task_data(task,context='base'):
    result=task.to_dict()
    if context in ('list','detail'): result['overdue']=overdue(task)
    if context=='list':
        result['user_name']=task.user.name if task.user else None
        result['category_name']=task.category.name if task.category else None
    if context=='user':
        result={key:result[key] for key in ('id','title','description','status','priority','created_at','due_date')}
        result['overdue']=overdue(task)
    return result
