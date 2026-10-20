"""Тренировки: задания, попытки, баллы (хранятся в памяти)."""

import logging
import random
import threading
import uuid
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import List, Optional

from conjugator.checker import check_answer
from conjugator.config import Settings
from conjugator.dictionary import PERSONS, Verb, VerbDictionary
from conjugator.errors import SessionFinished, SessionNotFinished, SessionNotFound

logger = logging.getLogger(__name__)

CORRECT = "correct"
INCORRECT = "incorrect"
OUT_OF_ATTEMPTS = "out_of_attempts"


@dataclass
class Task:
    verb: Verb
    person_index: int
    attempts: int = 0
    solved: bool = False
    wrong_answers: List[str] = field(default_factory=list)

    @property
    def person(self) -> str:
        return PERSONS[self.person_index]

    @property
    def expected(self) -> str:
        return self.verb.form(self.person_index)


@dataclass
class Session:
    id: str
    tasks: List[Task]
    max_attempts: int
    index: int = 0
    score: int = 0

    @property
    def finished(self) -> bool:
        return self.index >= len(self.tasks)

    @property
    def current_task(self) -> Optional[Task]:
        return None if self.finished else self.tasks[self.index]

    @property
    def percentage(self) -> float:
        return round(self.score / len(self.tasks) * 100, 1)

    def attempts_left(self, task: Task) -> int:
        return self.max_attempts - task.attempts


@dataclass(frozen=True)
class AnswerOutcome:
    outcome: str
    task: Task
    hint: Optional[str]


class SessionStore:
    def __init__(self, dictionary: VerbDictionary, settings: Settings):
        self._dictionary = dictionary
        self._settings = settings
        self._rng = random.Random(settings.random_seed)
        self._sessions: "OrderedDict[str, Session]" = OrderedDict()
        self._lock = threading.Lock()

    def __len__(self) -> int:
        return len(self._sessions)

    def start(self, tasks: Optional[int] = None) -> Session:
        verbs = self._dictionary.all()
        count = min(tasks or self._settings.tasks_per_session, len(verbs))
        with self._lock:
            chosen = self._rng.sample(verbs, count)
            session = Session(
                id=uuid.uuid4().hex,
                tasks=[Task(verb, self._rng.randrange(len(PERSONS))) for verb in chosen],
                max_attempts=self._settings.max_attempts,
            )
            self._sessions[session.id] = session
            while len(self._sessions) > self._settings.max_sessions:
                evicted_id, _ = self._sessions.popitem(last=False)
                logger.warning("Session %s evicted: limit of %s sessions reached",
                               evicted_id, self._settings.max_sessions)
        logger.info("Session %s started: %s tasks", session.id, count)
        return session

    def get(self, session_id: str) -> Session:
        session = self._sessions.get(session_id)
        if session is None:
            raise SessionNotFound(session_id)
        return session

    def answer(self, session_id: str, answer: str) -> AnswerOutcome:
        with self._lock:
            session = self.get(session_id)
            task = session.current_task
            if task is None:
                raise SessionFinished(session_id)

            task.attempts += 1
            result = check_answer(
                answer, task.expected, task.verb.conjugation, task.person_index,
                self._settings.accept_e_for_yo,
            )
            if result.correct:
                task.solved = True
                session.score += 1
                outcome = CORRECT
            else:
                task.wrong_answers.append(answer)
                outcome = INCORRECT if session.attempts_left(task) > 0 else OUT_OF_ATTEMPTS

            # Следующее задание — после верного ответа или последней попытки.
            if outcome != INCORRECT:
                session.index += 1

        logger.info("Session %s answer: %s/%s -> %s",
                    session_id, task.verb.infinitive, task.person, outcome)
        if session.finished and outcome != INCORRECT:
            logger.info("Session %s finished: score %s/%s (%s%%)",
                        session_id, session.score, len(session.tasks), session.percentage)
        return AnswerOutcome(outcome=outcome, task=task, hint=result.hint)

    def result(self, session_id: str) -> Session:
        session = self.get(session_id)
        if not session.finished:
            raise SessionNotFinished(session_id)
        return session
