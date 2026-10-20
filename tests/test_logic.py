"""Тесты логики без HTTP."""

import pytest

from conjugator.checker import check_answer, normalize
from conjugator.config import ConfigError, Settings
from conjugator.dictionary import CONJUGATIONS, PERSONS, Verb, VerbDictionary
from conjugator.errors import SessionNotFound, VerbNotFound
from conjugator.sessions import SessionStore


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("  Читаешь ", "читаешь"),
        ("живёшь", "живешь"),
        ("чита́ешь", "читаешь"),
        ("ты читаешь", "читаешь"),
    ],
)
def test_normalize(raw, expected):
    assert normalize(raw) == expected


def test_strict_yo_rejects_e():
    assert check_answer("живешь", "живёшь", "I", 1, accept_e_for_yo=True).correct
    assert not check_answer("живешь", "живёшь", "I", 1, accept_e_for_yo=False).correct


def test_hint_for_wrong_ending_first_conjugation():
    result = check_answer("читаишь", "читаешь", "I", 1)
    assert not result.correct
    assert "окончание" in result.hint and "-ешь" in result.hint


def test_hint_for_wrong_ending_second_conjugation():
    result = check_answer("говорют", "говорят", "II", 5)
    assert "-ат / -ят" in result.hint


def test_hint_for_wrong_stem_does_not_reveal_answer():
    result = check_answer("говару", "говорю", "II", 0)
    assert "основу" in result.hint
    assert "говорю" not in result.hint


def test_dictionary_file_is_valid():
    dictionary = VerbDictionary.from_file()
    assert len(dictionary) >= 21
    for verb in dictionary.all():
        assert len(verb.forms) == len(PERSONS)
        assert verb.conjugation in CONJUGATIONS
        assert all(form.strip() == form and form for form in verb.forms)


def test_dictionary_lookup_is_case_insensitive():
    dictionary = VerbDictionary.from_file()
    assert dictionary.get(" Читать ").infinitive == "читать"
    with pytest.raises(VerbNotFound):
        dictionary.get("абвгд")


def test_dictionary_rejects_duplicates():
    verb = Verb("знать", "I", "to know", ("знаю",) * 6)
    with pytest.raises(ValueError):
        VerbDictionary([verb, verb])


def test_store_evicts_oldest_sessions():
    store = SessionStore(VerbDictionary.from_file(), Settings(max_sessions=2, random_seed=1))
    first = store.start()
    store.start()
    store.start()
    assert len(store) == 2
    with pytest.raises(SessionNotFound):
        store.get(first.id)


def test_seed_makes_sessions_reproducible():
    dictionary = VerbDictionary.from_file()
    tasks_a = SessionStore(dictionary, Settings(random_seed=7)).start().tasks
    tasks_b = SessionStore(dictionary, Settings(random_seed=7)).start().tasks
    assert [(t.verb.infinitive, t.person_index) for t in tasks_a] == \
           [(t.verb.infinitive, t.person_index) for t in tasks_b]


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("MAX_ATTEMPTS", "5")
    monkeypatch.setenv("ACCEPT_E_FOR_YO", "false")
    monkeypatch.setenv("LOG_LEVEL", "debug")
    settings = Settings.from_env()
    assert settings.max_attempts == 5
    assert settings.accept_e_for_yo is False
    assert settings.log_level == "DEBUG"


@pytest.mark.parametrize("name, value", [("MAX_ATTEMPTS", "abc"), ("MAX_ATTEMPTS", "0"), ("LOG_LEVEL", "LOUD")])
def test_invalid_settings_raise_clear_error(monkeypatch, name, value):
    monkeypatch.setenv(name, value)
    with pytest.raises(ConfigError, match=name):
        Settings.from_env()
