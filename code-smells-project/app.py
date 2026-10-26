"""Composition only: importing does not open or seed a database."""
import os
from datetime import datetime, timezone

from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

import database
from routes import register_routes
from validators import InputError


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_mapping(SECRET_KEY=os.environ.get('SHOP_SECRET_KEY'),
        DATABASE=os.environ.get('SHOP_DATABASE', 'loja.db'), DEBUG=False, TOKEN_TTL=3600,
        LEGACY_PASSWORD_CUTOFF=os.environ.get('SHOP_LEGACY_PASSWORD_CUTOFF'),
        CLOCK=lambda: datetime.now(timezone.utc))
    if config:
        app.config.update(config)
    if not isinstance(app.config['SECRET_KEY'], str) or not app.config['SECRET_KEY']:
        raise RuntimeError('SHOP_SECRET_KEY deve ser configurada')
    if type(app.config['TOKEN_TTL']) is not int or app.config['TOKEN_TTL'] <= 0:
        raise RuntimeError('TOKEN_TTL deve ser um inteiro positivo')
    cutoff = app.config['LEGACY_PASSWORD_CUTOFF']
    if cutoff:
        try:
            if datetime.fromisoformat(cutoff).tzinfo is None:
                raise ValueError('timezone required')
        except (ValueError, TypeError) as exc:
            raise RuntimeError('SHOP_LEGACY_PASSWORD_CUTOFF requer ISO8601 com fuso') from exc
    CORS(app)
    database.init_app(app)
    register_routes(app)

    @app.errorhandler(InputError)
    def input_error(error):
        body = {'erro': str(error)}
        if error.business:
            body['sucesso'] = False
        return jsonify(body), 400

    @app.errorhandler(HTTPException)
    def http_error(error):
        if error.code in (400, 415):
            return jsonify({'erro': 'Dados inválidos'}), 400
        return error

    @app.errorhandler(Exception)
    def unexpected_error(error):
        app.logger.error('Falha interna no processamento (%s)', type(error).__name__)
        if request.endpoint == 'shop.health':
            return jsonify({'status':'erro', 'detalhes':'Erro interno do servidor'}), 500
        return jsonify({'erro': 'Erro interno do servidor'}), 500

    return app


if __name__ == '__main__':
    create_app().run(host=os.environ.get('SHOP_HOST', '127.0.0.1'),
        port=int(os.environ.get('SHOP_PORT', '5000')), debug=os.environ.get('SHOP_DEBUG') == '1',
        use_reloader=False)
