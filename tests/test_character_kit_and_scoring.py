import pytest
import os
import json
import tempfile
from fastapi.testclient import TestClient

from alibi.character import random_suspect, get_suspect_png_bytes, pick_traits, describe_traits
from alibi.game.scoring import calculate_score, get_detective_rank, RANK_TIERS
from alibi.game.session import GameManager
from alibi.llm.client import OllamaClient
from alibi.server import app

def test_character_generation_determinism():
    """Verify same seed produces identical character traits and identical PNG bytes."""
    seed = "2026-11-09"
    traits1, colors1 = pick_traits(seed)
    traits2, colors2 = pick_traits(seed)
    assert traits1 == traits2
    assert colors1 == colors2

    png_bytes1 = get_suspect_png_bytes(seed, scale=4, crt=True)
    png_bytes2 = get_suspect_png_bytes(seed, scale=4, crt=True)
    assert len(png_bytes1) > 500
    assert png_bytes1 == png_bytes2
    # Check PNG magic header
    assert png_bytes1[:8] == b"\x89PNG\r\n\x1a\n"

def test_character_trait_description():
    """Verify human-readable trait description generator."""
    seed = "case-test-123"
    traits, _ = pick_traits(seed)
    desc = describe_traits(traits)
    assert isinstance(desc, str)
    assert len(desc) > 0

def test_scoring_system_calculations():
    """Verify scoring logic with bonuses and difficulty multipliers."""
    # Classic win with 3 tokens left in 1 turn (quick bonus, flawless bonus)
    sc = calculate_score(
        won=True,
        remaining_tokens=3,
        turns_taken=1,
        hint_used=False,
        difficulty="classic",
        streak=5
    )
    assert sc["base"] == 1000
    assert sc["tokens_bonus"] == 750
    assert sc["quick_bonus"] == 500
    assert sc["flawless_bonus"] == 250
    assert sc["streak_bonus"] == 500
    assert sc["multiplier"] == 1.0
    assert sc["total"] == 3000

    # Hardboiled multiplier 1.5x
    sc_hard = calculate_score(
        won=True,
        remaining_tokens=2,
        turns_taken=2,
        hint_used=False,
        difficulty="hardboiled",
        streak=1
    )
    # (1000 + 500 + 500 + 250 + 100) * 1.5 = 2350 * 1.5 = 3525
    assert sc_hard["total"] == 3525

    # Lost game awards 0 points
    sc_lost = calculate_score(
        won=False,
        remaining_tokens=0,
        turns_taken=5,
        hint_used=True,
        difficulty="classic",
        streak=0
    )
    assert sc_lost["total"] == 0

def test_detective_rank_brackets():
    """Verify rank tiers based on career score."""
    assert get_detective_rank(0)["rank"] == "PATROL OFFICER"
    assert get_detective_rank(1500)["rank"] == "JUNIOR GUMSHOE"
    assert get_detective_rank(4500)["rank"] == "BEAT DETECTIVE"
    assert get_detective_rank(8000)["rank"] == "SENIOR INSPECTOR"
    assert get_detective_rank(12000)["rank"] == "CHIEF OF DETECTIVES"
    assert get_detective_rank(25000)["rank"] == "LEGENDARY NOIR INQUISITOR"

def test_memory_and_progress_persistence():
    """Verify memory system tracks solved challenges and prevents duplicate score inflation."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
        temp_save = tf.name

    try:
        # Initial save state
        initial_data = {
            "completed_dates": {},
            "games_played": 0,
            "games_won": 0,
            "current_streak": 0,
            "max_streak": 0,
            "total_score": 0,
            "high_score": 0,
            "last_played_date": None
        }
        with open(temp_save, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        client = OllamaClient()
        gm = GameManager(client=client, saves_path=temp_save)

        # Initially today is not completed
        assert gm.is_daily_completed("2026-11-09") is False

        # Mock a session
        from alibi.models.schema import Case, SuspectProfile, VerifiedFact, LiePlan
        dummy_case = Case(
            id="test-case-1",
            date="2026-11-09",
            title="The Grand Heist",
            crime_description="Someone took the antique ledger",
            setting="The Brass Manor",
            suspect=SuspectProfile(name="Silas Vance", occupation="Clerk", quirk="Twitches"),
            dossier=[
                VerifiedFact(id="f1", text="Rain fell at 8 PM"),
                VerifiedFact(id="f2", text="Ledger was locked at 9 PM"),
                VerifiedFact(id="f3", text="Vault was intact")
            ],
            truth_timeline=[],
            lie_plan=LiePlan(cover_story="I was asleep", weak_points=[])
        )
        gm.init_session(dummy_case, is_practice=False, difficulty="classic")
        gm.session.remaining_tokens = 3

        # Record victory
        score_info = gm._record_game_end(won=True)
        assert score_info["total"] > 0
        assert gm.is_daily_completed("2026-11-09") is True
        assert gm.progress_data["total_score"] == score_info["total"]
        assert gm.progress_data["current_streak"] == 1
        assert gm.progress_data["games_played"] == 1
        assert gm.progress_data["games_won"] == 1

        # Now simulate replaying the same day's case to ensure duplicate inflation is prevented
        gm.init_session(dummy_case, is_practice=False, difficulty="classic")
        gm.session.remaining_tokens = 4
        gm._record_game_end(won=True)

        # Games played and streak should NOT increment again for the same date
        assert gm.progress_data["games_played"] == 1
        assert gm.progress_data["current_streak"] == 1
    finally:
        if os.path.exists(temp_save):
            os.remove(temp_save)

def test_api_character_endpoint():
    """Verify /api/character/{seed}.png returns valid image/png response."""
    test_client = TestClient(app)
    resp = test_client.get("/api/character/2026-11-09.png")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"
    assert resp.content[:8] == b"\x89PNG\r\n\x1a\n"

def test_api_status_scoring_fields():
    """Verify /api/status returns new score, rank, and memory fields."""
    test_client = TestClient(app)
    resp = test_client.get("/api/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_score" in data
    assert "rank" in data
    assert "today_solved" in data
    assert "countdown_midnight" in data
    assert isinstance(data["total_score"], int)

