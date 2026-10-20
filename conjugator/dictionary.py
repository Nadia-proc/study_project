"""Словарь глаголов из data/verbs.json."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple, Union

from conjugator.errors import VerbNotFound

PERSONS: Tuple[str, ...] = ("я", "ты", "он/она/оно", "мы", "вы", "они")
CONJUGATIONS: Tuple[str, ...] = ("I", "II")
DEFAULT_VERBS_FILE = Path(__file__).parent / "data" / "verbs.json"


@dataclass(frozen=True)
class Verb:
    infinitive: str
    conjugation: str
    translation: str
    forms: Tuple[str, ...]

    def form(self, person_index: int) -> str:
        return self.forms[person_index]


def _parse_verb(item: dict) -> Verb:
    infinitive = item.get("infinitive", "?")
    forms = tuple(item.get("forms", ()))
    if len(forms) != len(PERSONS):
        raise ValueError(f"Verb {infinitive!r}: expected {len(PERSONS)} forms, got {len(forms)}")
    if item.get("conjugation") not in CONJUGATIONS:
        raise ValueError(f"Verb {infinitive!r}: unknown conjugation {item.get('conjugation')!r}")
    return Verb(
        infinitive=infinitive,
        conjugation=item["conjugation"],
        translation=item.get("translation", ""),
        forms=forms,
    )


class VerbDictionary:
    def __init__(self, verbs: Iterable[Verb]):
        self._verbs: Dict[str, Verb] = {}
        for verb in verbs:
            if verb.infinitive in self._verbs:
                raise ValueError(f"Duplicate verb {verb.infinitive!r}")
            self._verbs[verb.infinitive] = verb

    @classmethod
    def from_file(cls, path: Union[str, Path] = DEFAULT_VERBS_FILE) -> "VerbDictionary":
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return cls(_parse_verb(item) for item in data)

    def __len__(self) -> int:
        return len(self._verbs)

    def get(self, infinitive: str) -> Verb:
        verb = self._verbs.get(infinitive.strip().lower())
        if verb is None:
            raise VerbNotFound(infinitive)
        return verb

    def all(self) -> List[Verb]:
        return list(self._verbs.values())
