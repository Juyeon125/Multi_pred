from importlib import import_module

from flask import Flask

from app.database import Database
from app.misc.log import log


def register_extensions(flask_app: Flask):
    from app import extensions

    extensions.cors.init_app(flask_app)


def register_views(flask_app: Flask):
    from app.blueprints import app as a

    import_module(a.import_name)
    flask_app.register_blueprint(a)


def register_hooks(flask_app: Flask):
    from app.hooks.error import broad_exception_handler
    from app.hooks.request_context import after_request

    flask_app.after_request(after_request)
    flask_app.register_error_handler(Exception, broad_exception_handler)


def create_app(*config_cls) -> Flask:
    config_cls = [
        config() if isinstance(config, type) else config for config in config_cls
    ]

    log(
        message="Flask application initialized with {}".format(
            ", ".join([config.__class__.__name__ for config in config_cls])
        ),
        keyword="INFO",
    )

    flask_app = Flask(__name__)
    for config in config_cls:
        flask_app.config.from_object(config)

    register_extensions(flask_app)
    register_views(flask_app)
    register_hooks(flask_app)

    with flask_app.app_context():
        Database(config.DB_HOST, config.DB_USER, config.DB_PASSWORD, config.DB_DATABASE)

    return flask_app
