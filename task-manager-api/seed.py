"""Script para popular o banco com dados iniciais"""
from app import create_app
from database import db
from sqlalchemy import delete
from pathlib import Path
import argparse
from utils.domain import utcnow
from models.task import Task
from models.user import User
from models.category import Category
from models import store
from datetime import timedelta

def seed_data(app, replace=False, checkpoint=None):
    """Populate only an explicitly disposable database, atomically."""
    if not app.config.get('ALLOW_DISPOSABLE_SEED'):
        raise ValueError('Seed exige banco descartável explicitamente autorizado')
    checkpoint = checkpoint or (lambda stage: None)
    with app.app_context(), db.session.begin():
        if (store.count(User) or store.count(Task) or store.count(Category)) and not replace:
            raise ValueError('Banco não vazio; use replace apenas em dados descartáveis')

        db.session.execute(delete(Task))
        db.session.execute(delete(User))
        db.session.execute(delete(Category))
        db.session.flush()
        checkpoint('deleted')

        u1 = User()
        u1.name = 'João Silva'
        u1.email = 'joao@email.com'
        u1.set_password('1234')
        u1.role = 'admin'
        db.session.add(u1)

        u2 = User()
        u2.name = 'Maria Santos'
        u2.email = 'maria@email.com'
        u2.set_password('abcd')
        u2.role = 'user'
        db.session.add(u2)

        u3 = User()
        u3.name = 'Pedro Oliveira'
        u3.email = 'pedro@email.com'
        u3.set_password('pass')
        u3.role = 'manager'
        db.session.add(u3)

        db.session.flush()
        checkpoint('users')

        c1 = Category()
        c1.name = 'Backend'
        c1.description = 'Tarefas de backend'
        c1.color = '#3498db'
        db.session.add(c1)

        c2 = Category()
        c2.name = 'Frontend'
        c2.description = 'Tarefas de frontend'
        c2.color = '#2ecc71'
        db.session.add(c2)

        c3 = Category()
        c3.name = 'DevOps'
        c3.description = 'Tarefas de infraestrutura'
        c3.color = '#e74c3c'
        db.session.add(c3)

        c4 = Category()
        c4.name = 'Bug'
        c4.description = 'Correção de bugs'
        c4.color = '#e67e22'
        db.session.add(c4)

        db.session.flush()
        checkpoint('categories')

        tasks_data = [
            {'title': 'Implementar autenticação JWT', 'description': 'Adicionar autenticação real com JWT', 'status': 'pending', 'priority': 1, 'user_id': u1.id, 'category_id': c1.id, 'due_date': utcnow() - timedelta(days=3)},
            {'title': 'Criar tela de login', 'description': 'Tela de login responsiva', 'status': 'in_progress', 'priority': 2, 'user_id': u2.id, 'category_id': c2.id, 'due_date': utcnow() + timedelta(days=5)},
            {'title': 'Configurar CI/CD', 'description': 'Pipeline com GitHub Actions', 'status': 'done', 'priority': 2, 'user_id': u3.id, 'category_id': c3.id, 'tags': 'devops,ci,github'},
            {'title': 'Corrigir bug no filtro de busca', 'description': 'Filtro não funciona com caracteres especiais', 'status': 'pending', 'priority': 1, 'user_id': u1.id, 'category_id': c4.id, 'due_date': utcnow() - timedelta(days=1)},
            {'title': 'Adicionar paginação na API', 'description': 'Endpoints retornam todos os registros', 'status': 'pending', 'priority': 3, 'user_id': u1.id, 'category_id': c1.id, 'due_date': utcnow() + timedelta(days=10)},
            {'title': 'Escrever testes unitários', 'description': 'Cobertura mínima de 80%', 'status': 'pending', 'priority': 2, 'user_id': u2.id, 'category_id': c1.id},
            {'title': 'Documentar API com Swagger', 'description': 'Gerar documentação automática', 'status': 'cancelled', 'priority': 4, 'user_id': u3.id, 'category_id': c1.id},
            {'title': 'Refatorar models', 'description': 'Melhorar organização dos models', 'status': 'in_progress', 'priority': 3, 'user_id': u2.id, 'category_id': c1.id, 'tags': 'refactor,tech-debt'},
            {'title': 'Configurar monitoramento', 'description': 'Prometheus + Grafana', 'status': 'pending', 'priority': 4, 'user_id': u3.id, 'category_id': c3.id, 'due_date': utcnow() + timedelta(days=20)},
            {'title': 'Melhorar validações de input', 'description': 'Usar marshmallow ou pydantic', 'status': 'pending', 'priority': 3, 'user_id': u1.id, 'category_id': c1.id, 'tags': 'improvement,validation'},
        ]

        for td in tasks_data:
            t = Task()
            t.title = td['title']
            t.description = td['description']
            t.status = td['status']
            t.priority = td['priority']
            t.user_id = td['user_id']
            t.category_id = td['category_id']
            if 'due_date' in td:
                t.due_date = td['due_date']
            if 'tags' in td:
                t.tags = td['tags']
            db.session.add(t)

        db.session.flush()
        checkpoint('tasks')
        counts = {'users': store.count(User), 'categories': store.count(Category), 'tasks': store.count(Task)}
    return counts


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Seed somente para bancos descartáveis')
    parser.add_argument('--database', required=True)
    parser.add_argument('--disposable', action='store_true', required=True)
    parser.add_argument('--replace', action='store_true')
    args = parser.parse_args()
    path = Path(args.database).resolve()
    app = create_app({'SQLALCHEMY_DATABASE_URI': 'sqlite:///' + str(path), 'ALLOW_DISPOSABLE_SEED': args.disposable})
    with app.app_context():
        db.create_all()
    counts = seed_data(app, replace=args.replace)
    print('Seed concluído com sucesso:', counts)
