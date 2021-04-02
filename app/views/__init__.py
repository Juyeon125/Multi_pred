from typing import Union

from flask import Blueprint, Flask
from flask_restful import output_json
from pydantic import BaseModel


def _pydantic_safe_output_json(data: Union[BaseModel, dict, list], code, headers=None):
    if isinstance(data, BaseModel):
        data = data.dict()

    return output_json(data, code, headers)


def route(flask_app: Flask):
    handle_exception_func = flask_app.handle_exception
    handle_user_exception_func = flask_app.handle_user_exception

    bp = Blueprint("app", __name__)

    flask_app.register_blueprint(bp)

    flask_app.handle_exception = handle_exception_func
    flask_app.handle_user_exception = handle_user_exception_func
