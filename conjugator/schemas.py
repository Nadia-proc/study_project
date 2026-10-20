"""Модели запросов и ответов API."""

from typing import Annotated, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, StringConstraints

Outcome = Literal["correct", "incorrect", "out_of_attempts"]


class HomeResponse(BaseModel):
    message: str
    docs: str
    start: str


class HealthResponse(BaseModel):
    status: Literal["ok"]
    verbs_loaded: int
    active_sessions: int


class VersionResponse(BaseModel):
    name: str
    version: str


class VerbSummary(BaseModel):
    infinitive: str
    translation: str


class VerbList(BaseModel):
    count: int
    verbs: List[VerbSummary]


class VerbDetail(VerbSummary):
    forms: Dict[str, str] = Field(description="Форма глагола для каждого лица")


class StartSessionRequest(BaseModel):
    tasks: Optional[int] = Field(None, ge=1, le=50, description="Количество заданий")


class TaskOut(BaseModel):
    number: int
    infinitive: str
    translation: str
    person: str
    attempts_left: int


class SessionState(BaseModel):
    session_id: str
    total_tasks: int
    completed_tasks: int
    score: int
    finished: bool
    task: Optional[TaskOut] = Field(None, description="Текущее задание, null если тренировка завершена")


class AnswerRequest(BaseModel):
    answer: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]


class AnswerResponse(SessionState):
    outcome: Outcome
    message: str
    hint: Optional[str] = None
    correct_answer: Optional[str] = None


class Mistake(BaseModel):
    infinitive: str
    person: str
    your_answers: List[str]
    correct_answer: str
    solved: bool


class SessionResult(BaseModel):
    session_id: str
    score: int
    total_tasks: int
    percentage: float
    message: str
    mistakes: List[Mistake]
