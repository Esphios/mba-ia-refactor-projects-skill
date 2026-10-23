import os

from flask import Flask
from flask_cors import CORS

import database
from config import Config
from errors import register_error_handlers
from routes import ALL_BLUEPRINTS


def create_app(test_config=None):
    application = Flask(__name__)
    application.config.from_object(Config)
    if test_config:
        application.config.update(test_config)
    Config.validate(application.config)

    CORS(application)
    database.init_app(application)
    register_error_handlers(application)
    for blueprint in ALL_BLUEPRINTS:
        application.register_blueprint(blueprint)
    return application


app = create_app()


if __name__ == "__main__":
    app.run(
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "5000")),
        debug=app.config["DEBUG"],
    )
