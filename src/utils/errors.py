from enum import Enum
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class ErrorCode(str, Enum):
    INTERNAL_ERROR = "internal_error"
    VALIDATION_ERROR = "validation_error"
    NOT_IMPLEMENTED = "not_implemented"
    STORAGE_ERROR = "storage_error"


class AppException(StarletteHTTPException):
    def __init__(self, *, error_code: ErrorCode, message: str, status_code: int = HTTPStatus.BAD_REQUEST):
        self.error_code = error_code
        super().__init__(status_code=status_code, detail=message)


def format_error_response(error_code: ErrorCode, message: str) -> dict[str, Any]:
    return {"success": False, "error": error_code.value, "message": message}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(_: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=format_error_response(exc.error_code, str(exc.detail)))

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        details = "; ".join(f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}" for err in exc.errors())
        return JSONResponse(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            content=format_error_response(ErrorCode.VALIDATION_ERROR, details),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = ErrorCode.INTERNAL_ERROR if exc.status_code >= 500 else ErrorCode.VALIDATION_ERROR
        return JSONResponse(status_code=exc.status_code, content=format_error_response(code, str(exc.detail)))
