import sqlite3

from flask import jsonify
from werkzeug.exceptions import BadRequest, HTTPException


class APIError(Exception):
    def __init__(self, message, status_code=400, *, success=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.success = success


class NotFoundError(APIError):
    def __init__(self, message):
        super().__init__(message, 404)


class ConflictError(APIError):
    def __init__(self, message):
        super().__init__(message, 409)


def register_error_handlers(app):
    @app.errorhandler(APIError)
    def handle_api_error(error):
        payload = {"erro": error.message}
        if error.success is not None:
            payload["sucesso"] = error.success
        return jsonify(payload), error.status_code

    @app.errorhandler(BadRequest)
    def handle_bad_request(_error):
        return jsonify({"erro": "Dados inválidos"}), 400

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        response = error.get_response()
        response.data = app.json.dumps({'erro': error.name})
        response.content_type = 'application/json'
        return response

    @app.errorhandler(sqlite3.Error)
    def handle_database_error(error):
        app.logger.exception("Database operation failed", exc_info=error)
        return jsonify({"erro": "Erro interno"}), 500

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        app.logger.exception("Unexpected application error", exc_info=error)
        return jsonify({"erro": "Erro interno"}), 500
