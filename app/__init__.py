from importlib import import_module

from flask import Flask

from app import preprocess
from app.database import Database
from app.misc.log import log
from config.app_config import ProductionLevelConfig
from config.db_config import RemoteConfig


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
    # preprocess.preprocess_deepec()
    # preprocess.preprocess_ecpred()
    # preprocess.preprocess_ecami()
    # preprocess.preprocess_detect_v2()

    if len(config_cls) == 0:
        config_cls = (ProductionLevelConfig, RemoteConfig)

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
        c = flask_app.config
        Database(c['DB_HOST'], c['DB_USER'], c['DB_PASSWORD'], c['DB_DATABASE'])

    return flask_app
