from auth import authenticate, admin
from models import Category
from models import repository as repo
from utils.validation import body, category_fields

def listing():
    authenticate()
    return [dict(c.to_dict(),task_count=len(c.tasks)) for c in repo.categories()]

def write(data,cat_id=None):
    admin();data=body(data);category=repo.get(Category,cat_id) if cat_id else Category()
    values=category_fields(data,not cat_id)
    for key,value in values.items(): setattr(category,key,value)
    return repo.save(category).to_dict()

def remove(cat_id):
    admin();repo.delete(repo.get(Category,cat_id));return {'message':'Categoria deletada'}
