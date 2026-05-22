from fastapi import HTTPException, status


class QuBEException(Exception):
    """Base exception for QuBE application."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class AuthException(QuBEException):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class ForbiddenException(QuBEException):
    def __init__(self, message: str = "Access forbidden"):
        super().__init__(message, status.HTTP_403_FORBIDDEN)


class NotFoundException(QuBEException):
    def __init__(self, resource: str = "Resource"):
        super().__init__(f"{resource} not found", status.HTTP_404_NOT_FOUND)


class ValidationException(QuBEException):
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY)


class DatabaseException(QuBEException):
    def __init__(self, message: str = "Database error occurred"):
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR)


class AIServiceException(QuBEException):
    def __init__(self, message: str = "AI service error"):
        super().__init__(message, status.HTTP_503_SERVICE_UNAVAILABLE)


class UnsafeSQLException(QuBEException):
    def __init__(self, message: str = "SQL query contains unsafe operations"):
        super().__init__(message, status.HTTP_400_BAD_REQUEST)


def qube_exception_handler(request, exc: QuBEException):
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "error_type": type(exc).__name__},
    )
