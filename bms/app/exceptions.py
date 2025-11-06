import logging
from flask import jsonify
#from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)

class BMSException(Exception):
    status_code = 400

    def __init__(self, message: str | None = None):
        super().__init__(message or self.__class__.__name__)

    def to_dict(self):
        return {"error": self.__class__.__name__, "message": str(self)}


class NotFoundError(BMSException):
    status_code = 404


class DuplicateError(BMSException):
    status_code = 409

class DatabaseError(BMSException):
    status_code = 500

def register_exception_handlers(app):
    @app.errorhandler(Exception)
    def handle_all_errors(err):
        # If it's one of our simple exceptions, return its status and message
        if isinstance(err, BMSException):
            return jsonify({"error": err.__class__.__name__, "message": str(err)}), err.status_code

        # Otherwise log and return a generic 500 response
        logger.exception("Unhandled exception: %s", err)
        return jsonify({"error": "InternalServerError", "message": "An internal error occurred"}), 500
