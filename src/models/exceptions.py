from flask import jsonify
from werkzeug.exceptions import HTTPException

class AppError(Exception):
    """Base exception class for application errors."""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

def handle_app_error(error: AppError):
    """Handler for AppError exceptions."""
    response = jsonify({"error": str(error.message)})
    response.status_code = error.status_code
    return response

def handle_http_error(error: HTTPException):
    """Handler for HTTP exceptions."""
    response = jsonify({"error": str(error.description)})
    response.status_code = error.code
    return response 