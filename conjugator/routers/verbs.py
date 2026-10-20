"""Справочник глаголов."""

from fastapi import APIRouter, Depends

from conjugator.dependencies import get_dictionary
from conjugator.dictionary import PERSONS, VerbDictionary
from conjugator.schemas import VerbDetail, VerbList, VerbSummary

router = APIRouter(prefix="/verbs", tags=["verbs"])


@router.get("", response_model=VerbList)
def list_verbs(dictionary: VerbDictionary = Depends(get_dictionary)):
    verbs = dictionary.all()
    return VerbList(
        count=len(verbs),
        verbs=[VerbSummary(infinitive=v.infinitive, translation=v.translation) for v in verbs],
    )


@router.get("/{infinitive}", response_model=VerbDetail)
def get_verb(infinitive: str, dictionary: VerbDictionary = Depends(get_dictionary)):
    verb = dictionary.get(infinitive)
    return VerbDetail(
        infinitive=verb.infinitive,
        translation=verb.translation,
        forms=dict(zip(PERSONS, verb.forms)),
    )
