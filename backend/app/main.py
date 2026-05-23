from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.core.errors import AppError, build_error_response
from app.core.middleware import RequestLoggingMiddleware
from app.observability.logging import configure_logging
from app.routes import analyze, chat, health, tools


settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(
    title="AI Backend Playground",
    description=(
        "FastAPI backend for AI workflows, structured analysis, chat, "
        "and safe tools execution."
    ),
    version=settings.app_version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)

app.include_router(health.router)
app.include_router(analyze.router)
app.include_router(chat.router)
app.include_router(tools.router)


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return build_error_response(exc.code, exc.message, exc.status_code, exc.details)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    _: Request, exc: RequestValidationError
) -> JSONResponse:
    return build_error_response(
        "VALIDATION_ERROR",
        "Invalid request payload.",
        422,
        {"errors": exc.errors()},
    )


@app.exception_handler(Exception)
async def internal_error_handler(_: Request, exc: Exception) -> JSONResponse:
    return build_error_response(
        "INTERNAL_ERROR",
        "Unexpected internal error.",
        500,
        {"type": exc.__class__.__name__},
    )
