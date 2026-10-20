"""Сборка FastAPI-приложения."""

import logging
import time
from contextlib import asynccontextmanager
from dataclasses import asdict
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from conjugator import APP_NAME, __version__
from conjugator.config import Settings
from conjugator.dictionary import VerbDictionary
from conjugator.errors import TrainerError
from conjugator.logging_setup import setup_logging
from conjugator.routers import service, training, verbs
from conjugator.sessions import SessionStore

logger = logging.getLogger(__name__)


def create_app(settings: Optional[Settings] = None) -> FastAPI:
    settings = settings or Settings.from_env()
    setup_logging(settings.log_level)
    dictionary = VerbDictionary.from_file()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info("Starting %s v%s: %s verbs loaded, settings: %s",
                    APP_NAME, __version__, len(dictionary), asdict(settings))
        yield
        logger.info("Shutting down %s", APP_NAME)

    app = FastAPI(
        title=APP_NAME,
        description="Тренажёр спряжения русских глаголов в настоящем времени для иностранных студентов",
        version=__version__,
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.dictionary = dictionary
    app.state.store = SessionStore(dictionary, settings)

    app.include_router(service.router)
    app.include_router(verbs.router)
    app.include_router(training.router)

    @app.exception_handler(TrainerError)
    async def handle_trainer_error(request: Request, exc: TrainerError):
        logger.warning("%s %s: %s", request.method, request.url.path, exc.message)
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("%s %s failed", request.method, request.url.path)
            raise
        elapsed_ms = (time.perf_counter() - started) * 1000
        logger.info("%s %s -> %s (%.1f ms)",
                    request.method, request.url.path, response.status_code, elapsed_ms)
        return response

    return app
