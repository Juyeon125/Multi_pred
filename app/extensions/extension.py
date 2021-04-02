class BadRequestError(Exception):
    code = 400
    message = None

    def __init__(self, code=None, message=None):
        super(BadRequestError, self).__init__()

        if code is not None:
            self.code = code

        if message is not None:
            self.message = message


class NotFoundError(Exception):
    code = 404
    message = "Not Found Error!"

    def __init__(self, code=None, message=None):
        super(NotFoundError, self).__init__()

        if code is not None:
            self.code = code

        if message is not None:
            self.message = message
