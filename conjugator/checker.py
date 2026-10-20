"""Проверка ответов и подсказки."""

import unicodedata
from dataclasses import dataclass
from typing import Optional

from conjugator.dictionary import PERSONS

STRESS_MARK = "\u0301"  # знак ударения
PRONOUNS = {"я", "ты", "он", "она", "оно", "мы", "вы", "они"}

# Окончания по лицам: я, ты, он, мы, вы, они.
ENDINGS = {
    "I": (("у", "ю"), ("ешь", "ёшь"), ("ет", "ёт"), ("ем", "ём"), ("ете", "ёте"), ("ут", "ют")),
    "II": (("у", "ю"), ("ишь",), ("ит",), ("им",), ("ите",), ("ат", "ят")),
}


@dataclass(frozen=True)
class CheckResult:
    correct: bool
    hint: Optional[str] = None


def normalize(text: str, accept_e_for_yo: bool = True) -> str:
    """Убирает регистр, лишние пробелы, ударение, местоимение; ё → е."""
    text = unicodedata.normalize("NFC", text).replace(STRESS_MARK, "")
    words = text.casefold().split()
    if len(words) == 2 and words[0] in PRONOUNS:
        words = words[1:]
    result = " ".join(words)
    if accept_e_for_yo:
        result = result.replace("ё", "е")
    return result


def make_hint(answer: str, expected: str, conjugation: str, person_index: int) -> str:
    """Подсказка, не раскрывающая ответ."""
    person = PERSONS[person_index]
    if conjugation in ENDINGS:
        options = ENDINGS[conjugation][person_index]
        ending = next((e for e in options if expected.endswith(e)), None)
        if ending is not None:
            stem = expected[: -len(ending)]
            if answer.startswith(stem):
                shown = " / ".join(f"-{e}" for e in options)
                return f"Основа верная, проверь окончание: у этого глагола в форме «{person}» окончание {shown}."
    prefix = expected[:2]
    return f"Проверь основу глагола: правильная форма начинается на «{prefix}…»."


def check_answer(
    answer: str,
    expected: str,
    conjugation: str,
    person_index: int,
    accept_e_for_yo: bool = True,
) -> CheckResult:
    given = normalize(answer, accept_e_for_yo)
    target = normalize(expected, accept_e_for_yo)
    if given == target:
        return CheckResult(correct=True)
    return CheckResult(correct=False, hint=make_hint(given, target, conjugation, person_index))
