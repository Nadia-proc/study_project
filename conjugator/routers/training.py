"""Тренировки: старт, ответы, результат."""

from typing import Optional

from fastapi import APIRouter, Depends

from conjugator.dependencies import get_store
from conjugator.schemas import (
    AnswerRequest,
    AnswerResponse,
    Mistake,
    SessionResult,
    SessionState,
    StartSessionRequest,
    TaskOut,
)
from conjugator.sessions import CORRECT, INCORRECT, Session, SessionStore

router = APIRouter(prefix="/sessions", tags=["training"])


def _task_out(session: Session) -> Optional[TaskOut]:
    task = session.current_task
    if task is None:
        return None
    return TaskOut(
        number=session.index + 1,
        infinitive=task.verb.infinitive,
        translation=task.verb.translation,
        person=task.person,
        attempts_left=session.attempts_left(task),
    )


def _state(session: Session) -> dict:
    return {
        "session_id": session.id,
        "total_tasks": len(session.tasks),
        "completed_tasks": session.index,
        "score": session.score,
        "finished": session.finished,
        "task": _task_out(session),
    }


@router.post("", response_model=SessionState, status_code=201)
def start_session(
    payload: Optional[StartSessionRequest] = None,
    store: SessionStore = Depends(get_store),
):
    payload = payload or StartSessionRequest()
    session = store.start(tasks=payload.tasks)
    return SessionState(**_state(session))


@router.get("/{session_id}", response_model=SessionState)
def get_session(session_id: str, store: SessionStore = Depends(get_store)):
    return SessionState(**_state(store.get(session_id)))


@router.post("/{session_id}/answer", response_model=AnswerResponse)
def submit_answer(
    session_id: str,
    request: AnswerRequest,
    store: SessionStore = Depends(get_store),
):
    result = store.answer(session_id, request.answer)
    session = store.get(session_id)

    if result.outcome == CORRECT:
        message = "Правильно! Тренировка завершена." if session.finished else "Правильно! Идём дальше."
    elif result.outcome == INCORRECT:
        message = "Неправильно. Попробуй ещё раз."
    else:
        message = f"Попытки закончились. Правильный ответ: {result.task.expected}"

    return AnswerResponse(
        **_state(session),
        outcome=result.outcome,
        message=message,
        hint=result.hint,
        correct_answer=None if result.outcome == INCORRECT else result.task.expected,
    )


@router.get("/{session_id}/result", response_model=SessionResult)
def get_result(session_id: str, store: SessionStore = Depends(get_store)):
    session = store.result(session_id)
    total = len(session.tasks)
    return SessionResult(
        session_id=session.id,
        score=session.score,
        total_tasks=total,
        percentage=session.percentage,
        message=f"Твой результат: {session.score} из {total}",
        mistakes=[
            Mistake(
                infinitive=t.verb.infinitive,
                person=t.person,
                your_answers=t.wrong_answers,
                correct_answer=t.expected,
                solved=t.solved,
            )
            for t in session.tasks
            if t.wrong_answers
        ],
    )
