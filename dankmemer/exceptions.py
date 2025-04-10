class DankMemerException(Exception):
    """Base exception for all errors."""
    pass


class DankMemerHTTPException(DankMemerException):
    """Base exception for HTTP errors from Dank Alert's API."""
    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.status_code = status_code


class NotFoundException(DankMemerHTTPException):
    """Exception raised when a requested resource is not found (HTTP 404)."""
    pass


class ServerErrorException(DankMemerHTTPException):
    """Exception raised for server errors (HTTP 5xx)."""
    pass


class RateLimitException(DankMemerHTTPException):
    """Exception raised when rate limited (HTTP 429)."""
    pass


class BadRequestException(DankMemerHTTPException):
    """Exception raised for a bad request (HTTP 400)."""
    pass
