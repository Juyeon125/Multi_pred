import json
from http import HTTPStatus

from flask import current_app, jsonify, request, render_template
from pydantic import ValidationError
from werkzeug.exceptions import HTTPException

from app.extensions.extension import BadRequestError, NotFoundError


def broad_exception_handler(e: Exception):
    path = request.path
    if '.do' not in path:
        # View Error
        if isinstance(e, HTTPException):
            return render_template('error.html', user=None, message=e.description), e.code
        elif isinstance(e, BadRequestError):
            return render_template('error.html', user=None, message=e.message), e.code
        elif isinstance(e, NotFoundError):
            return render_template('error.html', user=None, message=e.message), e.code
        else:
            return render_template('error.html', user=None, message=e.message), 500

    else:
        # API Error
        if isinstance(e, HTTPException):
            message = e.description
            code = e.code

        elif isinstance(e, ValidationError):
            message = json.loads(e.json())
            code = HTTPStatus.BAD_REQUEST

        else:
            message = ""
            code = HTTPStatus.INTERNAL_SERVER_ERROR

            if current_app.debug:
                import traceback

                traceback.print_exc()

        return jsonify({"error": message}), code
