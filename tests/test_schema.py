import pytest
from pydantic import ValidationError
from alibi.models.schema import (
    Case, VerifiedFact, TimelineEvent, LiePlan, LieWeakPoint,
    SuspectProfile, AtomicClaim, Statement, SuspectResponse,
    JudgeEvaluation
)

def test_case_schema_valid():
    case_data = {
        "id": "case-test-1",
        "date": "2026-11-04",
        "title": "The Golden Spoon Heist",
        "crime_description": "The golden spoon was replaced with a plastic spork.",
        "setting": "The Museum",
        "suspect": {
            "name": "Barnaby Finch",
            "occupation": "Janitor",
            "quirk": "Speaks in rhymes"
        },
        "dossier": [
            {"id": "fact-1", "text": "Yellow boots were seen."},
            {"id": "fact-2", "text": "Power cut at 11:15 PM."},
            {"id": "fact-3", "text": "Spork receipt found."}
        ],
        "truth_timeline": [
            {"time": "11:15 PM", "event": "Swapped spoon."}
        ],
        "lie_plan": {
            "cover_story": "I was sleeping.",
            "weak_points": [
                {
                    "id": "wp-1",
                    "claim": "I wore brown boots.",
                    "conflicts_with": "fact-1",
                    "trigger_topics": ["boots"],
                    "planned_slip": "I only wear brown shoes!"
                }
            ]
        },
        "solution_contradictions": ["Claims brown boots but fact-1 states yellow boots."]
    }
    case = Case.model_validate(case_data)
    assert case.id == "case-test-1"
    assert len(case.dossier) == 3
    assert case.suspect.name == "Barnaby Finch"

def test_case_schema_missing_fields_raises():
    with pytest.raises(ValidationError):
        Case.model_validate({"id": "incomplete-case"})

def test_suspect_response_schema():
    valid_resp = {
        "inner_reasoning": "I need to deny being near the safe.",
        "spoken_answer": "I wasn't anywhere near the safe, matey!",
        "emotion": "defensive"
    }
    obj = SuspectResponse.model_validate(valid_resp)
    assert obj.emotion == "defensive"
    assert "safe" in obj.spoken_answer

def test_judge_evaluation_schema():
    data = {
        "claim_a_neutral": "Suspect claims he wore brown boots.",
        "claim_b_neutral": "Fact 1 states suspect wore yellow boots.",
        "logical_incompatibility": "Brown boots and yellow boots are mutually exclusive.",
        "verdict": "VALID",
        "narration": "The color clash gives up the ghost."
    }
    eval_obj = JudgeEvaluation.model_validate(data)
    assert eval_obj.verdict == "VALID"
