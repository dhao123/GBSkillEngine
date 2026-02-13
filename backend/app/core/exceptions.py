"""
GBSkillEngine 统一异常处理和错误响应规范
"""
from typing import Any, Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
import logging
import traceback

logger = logging.getLogger(__name__)


class ErrorResponse(BaseModel):
    """统一错误响应格式"""
    success: bool = False
    error_code: str
    message: str
    detail: Optional[Any] = None
    trace_id: Optional[str] = None


class AppException(Exception):
    """应用自定义异常基类"""
    def __init__(
        self,
        error_code: str,
        message: str,
        status_code: int = 400,
        detail: Any = None
    ):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(message)


# 预定义错误码
class ErrorCodes:
    # 通用错误 (1xxx)
    INTERNAL_ERROR = "E1000"
    VALIDATION_ERROR = "E1001"
    NOT_FOUND = "E1002"
    UNAUTHORIZED = "E1003"
    FORBIDDEN = "E1004"
    CONFLICT = "E1005"
    
    # 国标相关 (2xxx)
    STANDARD_NOT_FOUND = "E2001"
    STANDARD_ALREADY_EXISTS = "E2002"
    STANDARD_FILE_INVALID = "E2003"
    STANDARD_COMPILE_FAILED = "E2004"
    
    # Skill相关 (3xxx)
    SKILL_NOT_FOUND = "E3001"
    SKILL_ALREADY_EXISTS = "E3002"
    SKILL_DSL_INVALID = "E3003"
    SKILL_EXECUTION_FAILED = "E3004"
    
    # 物料梳理相关 (4xxx)
    MATERIAL_PARSE_FAILED = "E4001"
    NO_MATCHING_SKILL = "E4002"
    
    # 知识图谱相关 (5xxx)
    NEO4J_CONNECTION_ERROR = "E5001"
    GRAPH_QUERY_FAILED = "E5002"


# 预定义异常类
class NotFoundException(AppException):
    def __init__(self, message: str = "资源不存在", detail: Any = None):
        super().__init__(ErrorCodes.NOT_FOUND, message, 404, detail)


class ValidationException(AppException):
    def __init__(self, message: str = "数据验证失败", detail: Any = None):
        super().__init__(ErrorCodes.VALIDATION_ERROR, message, 400, detail)


class ConflictException(AppException):
    def __init__(self, message: str = "资源冲突", detail: Any = None):
        super().__init__(ErrorCodes.CONFLICT, message, 409, detail)


class StandardNotFoundException(AppException):
    def __init__(self, standard_id: int):
        super().__init__(
            ErrorCodes.STANDARD_NOT_FOUND,
            f"国标不存在: ID={standard_id}",
            404
        )


class SkillNotFoundException(AppException):
    def __init__(self, skill_id: str):
        super().__init__(
            ErrorCodes.SKILL_NOT_FOUND,
            f"Skill不存在: {skill_id}",
            404
        )


class SkillDSLInvalidException(AppException):
    def __init__(self, message: str, detail: Any = None):
        super().__init__(
            ErrorCodes.SKILL_DSL_INVALID,
            f"DSL配置无效: {message}",
            400,
            detail
        )


class MaterialParseException(AppException):
    def __init__(self, message: str, detail: Any = None):
        super().__init__(
            ErrorCodes.MATERIAL_PARSE_FAILED,
            f"物料梳理失败: {message}",
            500,
            detail
        )


def setup_exception_handlers(app: FastAPI) -> None:
    """配置全局异常处理器"""
    
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        """处理应用自定义异常"""
        logger.warning(f"AppException: {exc.error_code} - {exc.message}")
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error_code=exc.error_code,
                message=exc.message,
                detail=exc.detail
            ).model_dump()
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """处理HTTP异常"""
        error_code = {
            400: ErrorCodes.VALIDATION_ERROR,
            401: ErrorCodes.UNAUTHORIZED,
            403: ErrorCodes.FORBIDDEN,
            404: ErrorCodes.NOT_FOUND,
            409: ErrorCodes.CONFLICT,
        }.get(exc.status_code, ErrorCodes.INTERNAL_ERROR)
        
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error_code=error_code,
                message=str(exc.detail)
            ).model_dump()
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """处理请求验证错误"""
        errors = []
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            errors.append({
                "field": field,
                "message": error["msg"],
                "type": error["type"]
            })
        
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error_code=ErrorCodes.VALIDATION_ERROR,
                message="请求参数验证失败",
                detail=errors
            ).model_dump()
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """处理未捕获的异常"""
        logger.error(f"Unhandled exception: {exc}")
        logger.error(traceback.format_exc())
        
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error_code=ErrorCodes.INTERNAL_ERROR,
                message="服务器内部错误",
                detail=str(exc) if app.debug else None
            ).model_dump()
        )
