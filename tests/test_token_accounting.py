import pytest
from unittest.mock import MagicMock
from alibi.game.session import GameManager
from alibi.models.schema import Case, SuspectResponse, Statement, AccusationResult

def create_dummy_case():
    return Case(
        id="case-dummy",
        date="2026-11-04",
        title="Test Case",
        crime_description="Test crime",
        setting="Test setting",
        suspect={"name": "Test Suspect", "occupation": "Tester", "quirk": "Tests stuff"},
        dossier=[
            {"id": "fact-1", "text": "Fact 1 text"},
            {"id": "fact-2", "text": "Fact 2 text"},
            {"id": "fact-3", "text": "Fact 3 text"}
        ],
        truth_timeline=[{"time": "10:00", "event": "Event"}],
        lie_plan={"cover_story": "Alibi", "weak_points": []},
        solution_contradictions=[]
    )

def test_token_deduction_on_question():
    mock_client = MagicMock()
    mock_client.get_embeddings.return_value = [0.1] * 768
    gm = GameManager(mock_client, saves_path="saves/test_progress.json")
    gm.init_session(create_dummy_case(), is_practice=True)

    # Mock suspect response
    gm.suspect_agent.interrogate = MagicMock(return_value=SuspectResponse(
        inner_reasoning="None",
        spoken_answer="I was not there.",
        emotion="calm"
    ))
    gm.claim_extractor.extract_and_store = MagicMock(return_value=[])

    assert gm.session.remaining_tokens == 5
    success, err, stmt = gm.ask_question("Where were you?")
    assert success is True
    assert gm.session.remaining_tokens == 4
    assert len(gm.session.transcript) == 1

def test_token_depleted_ends_game():
    mock_client = MagicMock()
    mock_client.get_embeddings.return_value = [0.1] * 768
    gm = GameManager(mock_client, saves_path="saves/test_progress.json")
    gm.init_session(create_dummy_case(), is_practice=True)
    gm.session.remaining_tokens = 1

    gm.suspect_agent.interrogate = MagicMock(return_value=SuspectResponse(
        inner_reasoning="None", spoken_answer="No.", emotion="panicked"
    ))
    gm.claim_extractor.extract_and_store = MagicMock(return_value=[])

    success, err, stmt = gm.ask_question("Final question?")
    assert success is True
    assert gm.session.remaining_tokens == 0
    assert gm.session.game_over is True
    assert gm.session.won is False

def test_invalid_accusation_penalty():
    mock_client = MagicMock()
    mock_client.get_embeddings.return_value = [0.1] * 768
    gm = GameManager(mock_client, saves_path="saves/test_progress.json")
    gm.init_session(create_dummy_case(), is_practice=True)
    gm.session.remaining_tokens = 3

    # Mock judge returning INVALID
    gm.judge_agent.judge_accusation = MagicMock(return_value=AccusationResult(
        valid=False,
        verdict="INVALID",
        explanation="Not a contradiction.",
        highlighted_quote="I like tea",
        target_text="Power cut"
    ))

    result = gm.accuse("I like tea", "Power cut")
    assert result.valid is False
    assert gm.session.remaining_tokens == 2
