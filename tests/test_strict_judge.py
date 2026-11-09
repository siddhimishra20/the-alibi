import os
import pytest
from alibi.llm.client import OllamaClient
from alibi.models.schema import Case, AccusationResult, JudgeEvaluation
from alibi.game.session import GameManager
from alibi.agents.case_architect import CaseArchitectAgent
from alibi.agents.judge import ContradictionJudgeAgent
from alibi.rag.store import RAGStore

def test_judge_evaluation_schema_normalization():
    """Verify that JudgeEvaluation normalizes various casing and key formats from LLMs."""
    # Test lowercase snake_case
    eval1 = JudgeEvaluation.model_validate({
        "claim_a_neutral": "Suspect had tea",
        "claim_b_neutral": "Rain outside",
        "logical_incompatibility": "None",
        "verdict": "INVALID",
        "narration": "Tea does not stop the rain."
    })
    assert eval1.verdict == "INVALID"
    assert eval1.claim_a_neutral == "Suspect had tea"

    # Test capitalized spaced keys (common LLM behavior)
    eval2 = JudgeEvaluation.model_validate({
        "Claim A": "Suspect had tea",
        "Claim B": "Rain outside",
        "Mutual Exclusivity": "False",
        "Verdict": "INVALID",
        "Narration": "Circumstantial."
    })
    assert eval2.verdict == "INVALID"
    assert eval2.claim_a_neutral == "Suspect had tea"
    assert eval2.narration == "Circumstantial."

    # Test default fallback when verdict is ambiguous
    eval3 = JudgeEvaluation.model_validate({
        "Verdict": "maybe",
        "reason": "Not convinced"
    })
    assert eval3.verdict == "INVALID"

def test_deterministic_fallback_strictness():
    """Verify that deterministic fallback does not produce false positives on stop-words or circumstantial statements."""
    client = OllamaClient()
    rag = RAGStore(session_id="test_fallback", client=client)
    judge = ContradictionJudgeAgent(client=client, rag_store=rag)
    architect = CaseArchitectAgent(client)
    case_obj = Case.model_validate(architect.fallback_cases[0])

    # Quote with common words: "I was drinking tea at home with the cat"
    # Target: "Canary-yellow boots size 10 were recovered from the muddy flower bed behind the museum."
    verdict, exp = judge._deterministic_contradiction_check(
        quote="I was drinking tea at home with the cat",
        target="Canary-yellow boots size 10 were recovered from the muddy flower bed behind the museum.",
        case=case_obj
    )
    assert verdict == "INVALID", f"Expected INVALID, got {verdict}: {exp}"

    verdict2, exp2 = judge._deterministic_contradiction_check(
        quote="I walked past the hardware store on my evening stroll.",
        target="Store receipt shows wire cutters purchased at 8:45 PM.",
        case=case_obj
    )
    assert verdict2 == "INVALID", f"Expected INVALID, got {verdict2}: {exp2}"

def test_judge_agent_strict_verdicts_with_llm():
    """Verify that JudgeAgent LLM rules INVALID on irrelevant claims and VALID on true contradictions."""
    client = OllamaClient()
    connected, _ = client.verify_models()
    if not connected:
        pytest.skip("Ollama not connected")

    rag = RAGStore(session_id="test_llm_judge", client=client)
    judge = ContradictionJudgeAgent(client=client, rag_store=rag)
    architect = CaseArchitectAgent(client)
    case_obj = Case.model_validate(architect.fallback_cases[0])

    # 1. Irrelevant accusation MUST be INVALID
    res_irrelevant = judge.judge_accusation(
        quote="I was quietly drinking chamomile tea in my kitchen all evening.",
        target_text="A single canary-yellow boot print size 10 was preserved in the wet flowerbed.",
        case=case_obj,
        is_dossier_fact=True
    )
    assert res_irrelevant.valid is False
    assert res_irrelevant.verdict == "INVALID"
    assert "tea" in res_irrelevant.explanation.lower() or "contradict" in res_irrelevant.explanation.lower() or "coexist" in res_irrelevant.explanation.lower() or len(res_irrelevant.explanation) > 0

    # 2. Direct contradiction MUST be VALID
    res_valid = judge.judge_accusation(
        quote="I have never owned or put on a pair of canary-yellow boots in my entire life, I only wear black wingtips.",
        target_text="A single canary-yellow boot print size 10 was preserved in the wet flowerbed.",
        case=case_obj,
        is_dossier_fact=True
    )
    assert res_valid.valid is True
    assert res_valid.verdict == "VALID"
    assert res_valid.breakdown_confession is not None
    assert len(res_valid.breakdown_confession) > 0

def test_accusation_failure_penalizes_tokens_and_causes_loss():
    """Verify that making a failed accusation deducts tokens and triggers defeat when tokens reach 0."""
    client = OllamaClient()
    test_saves = "saves/test_failed_accuse_progress.json"
    if os.path.exists(test_saves):
        os.remove(test_saves)

    gm = GameManager(client, saves_path=test_saves)
    architect = CaseArchitectAgent(client)
    case_obj = Case.model_validate(architect.fallback_cases[0])

    # Initialize classic session with 5 tokens
    gm.init_session(case_obj, difficulty="classic", is_practice=True)
    assert gm.session.remaining_tokens == 5
    assert gm.session.game_over is False

    # Mock the judge to return an INVALID accusation
    class MockInvalidJudge:
        def judge_accusation(self, quote, target_text, case, is_dossier_fact=True):
            return AccusationResult(
                valid=False,
                verdict="INVALID",
                explanation="The court finds no direct logical clash.",
                highlighted_quote=quote,
                target_text=target_text
            )

    gm.judge_agent = MockInvalidJudge()

    # 1st failed accusation: 5 -> 4 tokens
    res1 = gm.accuse(
        quote="I like muffins.",
        target_text="The safe door was pried open.",
        is_dossier_fact=True
    )
    assert res1.valid is False
    assert gm.session.remaining_tokens == 4
    assert gm.session.game_over is False
    assert gm.session.won is False

    # Deplete down to 1 token
    gm.session.remaining_tokens = 1

    # Final failed accusation with 1 token left: 1 -> 0 tokens -> GAME OVER (LOST)
    res2 = gm.accuse(
        quote="I like muffins.",
        target_text="The safe door was pried open.",
        is_dossier_fact=True
    )
    assert res2.valid is False
    assert gm.session.remaining_tokens == 0
    assert gm.session.game_over is True
    assert gm.session.won is False

    # Clean up test file
    if os.path.exists(test_saves):
        os.remove(test_saves)

def test_hardboiled_failed_accusation_penalty():
    """Verify that on hardboiled difficulty, a failed accusation deducts 2 tokens."""
    client = OllamaClient()
    test_saves = "saves/test_hardboiled_penalty.json"
    if os.path.exists(test_saves):
        os.remove(test_saves)

    gm = GameManager(client, saves_path=test_saves)
    architect = CaseArchitectAgent(client)
    case_obj = Case.model_validate(architect.fallback_cases[0])

    gm.init_session(case_obj, difficulty="hardboiled", is_practice=True)
    assert gm.session.remaining_tokens == 3  # hardboiled starts with 3 tokens

    class MockInvalidJudge:
        def judge_accusation(self, quote, target_text, case, is_dossier_fact=True):
            return AccusationResult(
                valid=False,
                verdict="INVALID",
                explanation="No proof.",
                highlighted_quote=quote,
                target_text=target_text
            )

    gm.judge_agent = MockInvalidJudge()

    # Failed accusation on hardboiled should cost 2 tokens: 3 -> 1
    res = gm.accuse(
        quote="Irrelevant statement.",
        target_text="Target fact.",
        is_dossier_fact=True
    )
    assert res.valid is False
    assert gm.session.remaining_tokens == 1
    assert gm.session.game_over is False

    # Second failed accusation: 1 -> 0 (clamped to 0) -> GAME OVER (LOST)
    res2 = gm.accuse(
        quote="Irrelevant statement 2.",
        target_text="Target fact.",
        is_dossier_fact=True
    )
    assert res2.valid is False
    assert gm.session.remaining_tokens == 0
    assert gm.session.game_over is True
    assert gm.session.won is False

    if os.path.exists(test_saves):
        os.remove(test_saves)
