from fastapi import HTTPException, status


class ApplicationError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(f"ApplicationError: {message}")


class APIError(HTTPException):
    def __init__(self, status_code: int, code: str, message: str):
        detail = {"error": {"code": code, "message": message}}
        super().__init__(status_code=status_code, detail=detail)


class BadRequestError(APIError):
    def __init__(self, code: str = "INVALID_REQUEST", message: str = "Bad request"):
        super().__init__(status.HTTP_400_BAD_REQUEST, code, message)


class UnauthorizedError(APIError):
    def __init__(self, code: str = "UNAUTHORIZED", message: str = "Not authenticated"):
        super().__init__(status.HTTP_401_UNAUTHORIZED, code, message)


class ForbiddenError(APIError):
    def __init__(self, code: str = "FORBIDDEN", message: str = "Access forbidden"):
        super().__init__(status.HTTP_403_FORBIDDEN, code, message)


class NotFoundError(APIError):
    def __init__(self, code: str = "NOT_FOUND", message: str = "Resource not found"):
        super().__init__(status.HTTP_404_NOT_FOUND, code, message)


class ConflictError(APIError):
    def __init__(self, code: str = "CONFLICT", message: str = "Resource conflict"):
        super().__init__(status.HTTP_409_CONFLICT, code, message)


class InternalServerError(APIError):
    def __init__(self, code: str = "INTERNAL_ERROR", message: str = "Internal server error"):
        super().__init__(status.HTTP_500_INTERNAL_SERVER_ERROR, code, message)
