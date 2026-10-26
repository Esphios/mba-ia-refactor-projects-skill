"""Composition root. Importing this module never opens or creates a database."""
import os
from datetime import datetime
import click
from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy.exc import SQLAlchemyError
from database import db
from utils.errors import ApiError


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', 'sqlite:///tasks.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY=os.environ.get('SECRET_KEY'),
        TOKEN_MAX_AGE=int(os.environ.get('TOKEN_MAX_AGE', '3600')),
        LEGACY_MD5_CUTOFF=os.environ.get('LEGACY_MD5_CUTOFF'),
        SMTP_ENABLED=False,
    )
    if config:
        app.config.update(config)
    if not app.config['SECRET_KEY']:
        raise ValueError('SECRET_KEY deve ser configurada')
    if app.config['TOKEN_MAX_AGE'] <= 0:
        raise ValueError('TOKEN_MAX_AGE deve ser positivo')
    cutoff = app.config.get('LEGACY_MD5_CUTOFF')
    if cutoff and datetime.fromisoformat(cutoff).tzinfo is not None:
        raise ValueError('LEGACY_MD5_CUTOFF deve usar UTC sem offset')
    CORS(app)
    db.init_app(app)
    from routes.task_routes import task_bp
    from routes.user_routes import user_bp
    from routes.report_routes import report_bp
    for blueprint in (task_bp, user_bp, report_bp):
        app.register_blueprint(blueprint)

    @app.get('/health')
    def health():
        return {'status': 'ok', 'timestamp': str(datetime.now())}

    @app.get('/')
    def index():
        return {'message': 'Task Manager API', 'version': '1.0'}

    @app.cli.command('init-db')
    def init_db():
        """Create missing tables explicitly; never drop or seed existing data."""
        db.create_all()
        click.echo('Schema inicializado; dados existentes preservados.')

    @app.errorhandler(ApiError)
    def api_error(error):
        db.session.rollback()
        return jsonify({'error': error.message}), error.status

    @app.errorhandler(SQLAlchemyError)
    def database_error(error):
        db.session.rollback()
        app.logger.error('Database operation failed (%s)', type(error).__name__)
        messages = {
            'tasks.create_task': 'Erro ao criar task', 'tasks.update_task': 'Erro ao atualizar',
            'tasks.delete_task': 'Erro ao deletar', 'users.create_user': 'Erro ao criar usuário',
            'users.update_user': 'Erro ao atualizar', 'users.delete_user': 'Erro ao deletar',
            'reports.create_category': 'Erro ao criar categoria', 'reports.update_category': 'Erro ao atualizar',
            'reports.delete_category': 'Erro ao deletar',
        }
        return jsonify({'error': messages.get(request.endpoint, 'Erro interno')}), 500

    return app


if __name__ == '__main__':
    create_app().run(debug=False, host=os.environ.get('HOST', '127.0.0.1'), port=int(os.environ.get('PORT', '5000')))
