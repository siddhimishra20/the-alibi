import os
import pytest
from alibi.llm.client import OllamaClient
from alibi.models.schema import Case
from alibi.game.session import GameManager
from alibi.agents.case_architect import CaseArchitectAgent

def test_full_winning_session_lifecycle():
    client = OllamaClient()
    connected, _ = client.verify_models()
    if not connected:
        pytest.skip("Ollama not connected")

    gm = GameManager(client, saves_path="saves/test_gameplay_progress.json")
    architect = CaseArchitectAgent(client)
    
    # Load fallback case 1 (The Golden Spoon Heist)
    case = architect.fallback_cases[0]
    from alibi.models.schema import Case
    case_obj = Case.model_validate(case)

    # Initialize game
    gm.init_session(case_obj, is_practice=True)
    assert gm.session.remaining_tokens == 5
    assert gm.session.game_over is False

    # Ask a question touching a weak point (shoes/boots)
    success, err, stmt = gm.ask_question("What kind of shoes were you wearing last night?")
    assert success is True
    assert gm.session.remaining_tokens == 4
    assert len(gm.session.transcript) == 1
    assert stmt.answer is not None
    assert len(gm.session.ledger) > 0

    # Accuse with the contradiction
    # Quote from suspect contradicts fact-1 (canary-yellow boots)
    quote = stmt.answer
    target_fact = case_obj.dossier[0].text # Fact 1: Canary-yellow boots
    result = gm.accuse(quote=quote, target_text=target_fact, is_dossier_fact=True)

    # Verify accusation outcome
    assert result.verdict in ["VALID", "INVALID"]
    if result.valid:
        assert gm.session.won is True
        assert gm.session.game_over is True
        assert gm.session.accusation_result is not None
        share_grid = gm.generate_share_grid()
        assert "THE ALIBI" in share_grid

def test_losing_session_depleted_tokens():
    client = OllamaClient()
    connected, _ = client.verify_models()
    if not connected:
        pytest.skip("Ollama not connected")

    gm = GameManager(client, saves_path="saves/test_gameplay_progress.json")
    architect = CaseArchitectAgent(client)
    case_obj = Case.model_validate(architect.fallback_cases[0])

    gm.init_session(case_obj, is_practice=True)
    gm.session.remaining_tokens = 1

    # Ask question to deplete last token
    success, err, stmt = gm.ask_question("Tell me anything.")
    assert success is True
    assert gm.session.remaining_tokens == 0
    assert gm.session.game_over is True
    assert gm.session.won is False
