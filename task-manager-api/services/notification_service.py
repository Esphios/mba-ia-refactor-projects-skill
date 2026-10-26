"""Optional email integration, disabled without an injected transport."""
from utils.domain import utcnow


class NotificationService:
    def __init__(self, transport=None):
        self.notifications = []
        self.transport = transport

    def send_email(self, to, subject, body):
        return bool(self.transport(to, subject, body)) if self.transport else False

    def notify_task_assigned(self, user, task):
        self.send_email(user.email, f'Nova task atribuída: {task.title}',
            f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você.\n\nPrioridade: {task.priority}\nStatus: {task.status}")
        self.notifications.append({'type': 'task_assigned', 'user_id': user.id,
            'task_id': task.id, 'timestamp': utcnow()})

    def notify_task_overdue(self, user, task):
        self.send_email(user.email, f'Task atrasada: {task.title}',
            f"Olá {user.name},\n\nA task '{task.title}' está atrasada!\n\nData limite: {task.due_date}")

    def get_notifications(self, user_id):
        return [item for item in self.notifications if item['user_id'] == user_id]
