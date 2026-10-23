from flask import Flask
from sqlalchemy import text
from database import db
from config import load_config
from errors import register_errors
from utils.dates import utc_naive

def create_app(config=None):
    app=Flask(__name__)
    app.config.update(load_config())
    if config: app.config.update(config)
    if not app.config.get('SECRET_KEY'): raise RuntimeError('Configure SECRET_KEY')
    db.init_app(app)
    from routes.task_routes import task_bp
    from routes.user_routes import user_bp
    from routes.report_routes import report_bp
    from routes.category_routes import category_bp
    for blueprint in (task_bp,user_bp,report_bp,category_bp): app.register_blueprint(blueprint)
    register_errors(app)
    @app.get('/')
    def index(): return {'message':'Task Manager API','version':'1.0'}
    @app.get('/health')
    def health():
        try: db.session.execute(text('SELECT 1'))
        except Exception:
            db.session.rollback()
            return {'error':'Banco indisponível'},503
        return {'status':'ok','timestamp':str(utc_naive())}
    @app.cli.command('init-db')
    def init_db(): db.create_all()
    return app

if __name__=='__main__':
    import os
    create_app().run(host='127.0.0.1',port=int(os.getenv('PORT','5000')),debug=False)
