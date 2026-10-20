"""Служебные маршруты: /, /health, /version."""

from fastapi import APIRouter, Depends

from conjugator import APP_NAME, __version__
from conjugator.dependencies import get_dictionary, get_store
from conjugator.dictionary import VerbDictionary
from conjugator.schemas import HealthResponse, HomeResponse, VersionResponse
from conjugator.sessions import SessionStore

router = APIRouter(tags=["service"])


@router.get("/", response_model=HomeResponse)
def home():
    return {
        "message": f"Добро пожаловать в {APP_NAME}! Тренажёр спряжения русских глаголов.",
        "docs": "/docs",
        "start": "POST /sessions",
    }


@router.get("/health", response_model=HealthResponse)
def health(
    dictionary: VerbDictionary = Depends(get_dictionary),
    store: SessionStore = Depends(get_store),
):
    return {"status": "ok", "verbs_loaded": len(dictionary), "active_sessions": len(store)}


@router.get("/version", response_model=VersionResponse)
def version():
    return {"name": APP_NAME, "version": __version__}
