from flask import jsonify
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException
from database import db

class APIError(Exception):
    def __init__(self,message,status=400):
        self.message=message; self.status=status

def register_errors(app):
    @app.errorhandler(APIError)
    def expected(error):
        db.session.rollback()
        return jsonify(error=error.message),error.status
    @app.errorhandler(HTTPException)
    def http(error):
        return jsonify(error=error.name),error.code
    @app.errorhandler(SQLAlchemyError)
    def storage(error):
        db.session.rollback()
        return jsonify(error='Erro de persistência'),500
    @app.errorhandler(Exception)
    def unexpected(error):
        db.session.rollback()
        return jsonify(error='Erro interno'),500
