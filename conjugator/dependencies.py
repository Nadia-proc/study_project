"""Зависимости роутеров: объекты из app.state."""

from fastapi import Request

from conjugator.config import Settings
from conjugator.dictionary import VerbDictionary
from conjugator.sessions import SessionStore


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_dictionary(request: Request) -> VerbDictionary:
    return request.app.state.dictionary


def get_store(request: Request) -> SessionStore:
    return request.app.state.store
