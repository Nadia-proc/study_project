"""Тесты API."""

import pytest
from fastapi.testclient import TestClient

from conjugator import __version__
from conjugator.config import Settings
from conjugator.main import create_app


@pytest.fixture
def client():
    app = create_app(Settings(tasks_per_session=3, max_attempts=3, random_seed=42))
    with TestClient(app) as test_client:
        yield test_client


def correct_form(client, task):
    forms = client.get(f"/verbs/{task['infinitive']}").json()["forms"]
    return forms[task["person"]]


def start(client, **body):
    response = client.post("/sessions", json=body or None)
    assert response.status_code == 201
    return response.json()


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["verbs_loaded"] > 0


def test_version(client):
    response = client.get("/version")
    assert response.status_code == 200
    assert response.json()["version"] == __version__


def test_home_points_to_docs(client):
    assert client.get("/").json()["docs"] == "/docs"


def test_list_verbs(client):
    data = client.get("/verbs").json()
    assert data["count"] == len(data["verbs"]) > 0


def test_get_verb(client):
    response = client.get("/verbs/говорить")
    assert response.status_code == 200
    assert response.json()["forms"]["ты"] == "говоришь"
    assert response.json()["forms"]["они"] == "говорят"


def test_get_unknown_verb_returns_404(client):
    response = client.get("/verbs/абвгд")
    assert response.status_code == 404
    assert "не найден" in response.json()["detail"]


def test_full_session_with_correct_answers(client):
    session = start(client)
    assert session["total_tasks"] == 3

    state = session
    while not state["finished"]:
        answer = correct_form(client, state["task"])
        state = client.post(f"/sessions/{session['session_id']}/answer", json={"answer": answer}).json()
        assert state["outcome"] == "correct"

    result = client.get(f"/sessions/{session['session_id']}/result").json()
    assert result["score"] == 3
    assert result["percentage"] == 100.0
    assert result["mistakes"] == []


def test_wrong_answer_gives_hint_and_keeps_task(client):
    session = start(client)
    response = client.post(f"/sessions/{session['session_id']}/answer", json={"answer": "неправильно"})
    data = response.json()
    assert response.status_code == 200
    assert data["outcome"] == "incorrect"
    assert data["hint"]
    assert data["correct_answer"] is None
    assert data["task"]["attempts_left"] == 2
    assert data["task"]["infinitive"] == session["task"]["infinitive"]


def test_out_of_attempts_reveals_answer(client):
    session = start(client)
    url = f"/sessions/{session['session_id']}/answer"
    for _ in range(2):
        client.post(url, json={"answer": "мимо"})
    data = client.post(url, json={"answer": "мимо"}).json()
    assert data["outcome"] == "out_of_attempts"
    assert data["correct_answer"] == correct_form(client, session["task"])
    assert data["completed_tasks"] == 1


def test_session_size_from_request(client):
    session = start(client, tasks=5)
    assert session["total_tasks"] == 5


def test_session_size_out_of_range_returns_422(client):
    assert client.post("/sessions", json={"tasks": 0}).status_code == 422


def test_unknown_session_returns_404(client):
    assert client.get("/sessions/nope").status_code == 404
    assert client.post("/sessions/nope/answer", json={"answer": "знаю"}).status_code == 404


def test_result_before_finish_returns_400(client):
    session = start(client)
    assert client.get(f"/sessions/{session['session_id']}/result").status_code == 400


def test_answer_after_finish_returns_400(client):
    session = start(client, tasks=1)
    url = f"/sessions/{session['session_id']}/answer"
    client.post(url, json={"answer": correct_form(client, session["task"])})
    assert client.post(url, json={"answer": "знаю"}).status_code == 400


def test_empty_answer_returns_422(client):
    session = start(client)
    response = client.post(f"/sessions/{session['session_id']}/answer", json={"answer": "   "})
    assert response.status_code == 422


def test_entrypoint_exposes_app():
    import app_final

    assert app_final.app.title == "Russian Verb Trainer"
