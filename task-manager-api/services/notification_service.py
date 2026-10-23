import os
import smtplib
from email.message import EmailMessage
from utils.dates import utc_naive

class NotificationService:
    def __init__(self,transport=None):
        self.notifications=[]
        self.transport=transport or smtplib.SMTP
        self.email_host=os.getenv('SMTP_HOST')
        self.email_port=int(os.getenv('SMTP_PORT','587'))
        self.email_user=os.getenv('SMTP_USER')
        self.email_password=os.getenv('SMTP_PASSWORD')
        self.enabled=os.getenv('SMTP_ENABLED','false').lower()=='true'

    def send_email(self,to,subject,body):
        if not self.enabled or not self.email_host or not self.email_user: return False
        message=EmailMessage();message['Subject']=subject;message['From']=self.email_user;message['To']=to;message.set_content(body)
        try:
            with self.transport(self.email_host,self.email_port,timeout=10) as server:
                server.starttls()
                if self.email_password: server.login(self.email_user,self.email_password)
                server.send_message(message)
            return True
        except (OSError,smtplib.SMTPException): return False

    def notify_task_assigned(self,user,task):
        self.send_email(user.email,f'Nova task atribuída: {task.title}',f'Olá {user.name}, task: {task.title}')
        self.notifications.append(dict(type='task_assigned',user_id=user.id,task_id=task.id,timestamp=utc_naive()))

    def notify_task_overdue(self,user,task):
        self.send_email(user.email,f'Task atrasada: {task.title}',str(task.due_date))

    def get_notifications(self,user_id):
        return [n for n in self.notifications if n['user_id']==user_id]
