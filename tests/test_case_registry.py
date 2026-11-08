import os
import json
import pytest
from alibi.game.registry import CaseRegistry

def test_registry_registration_and_no_duplicates(tmp_path):
    reg_path = tmp_path / "case_registry.json"
    cases_dir = tmp_path / "cases"
    registry = CaseRegistry(registry_path=str(reg_path), cases_dir=str(cases_dir))

    case_1 = {
        "id": "case-2026-11-01",
        "title": "The Golden Spoon Heist",
        "suspect": {"name": "Barnaby Finch"},
        "setting": "Metropolitan Museum"
    }

    registry.register_case("2026-11-01", case_1, seed_id="crime-01")

    assert registry.is_date_registered("2026-11-01") is True
    assert registry.is_date_registered("2026-11-02") is False
    assert "crime-01" in registry.get_used_seed_ids()

    # Re-registering shouldn't duplicate seed in list
    registry.register_case("2026-11-01", case_1, seed_id="crime-01")
    assert registry.get_used_seed_ids().count("crime-01") == 1

def test_registry_archive_listing_with_progress(tmp_path):
    reg_path = tmp_path / "case_registry.json"
    cases_dir = tmp_path / "cases"
    registry = CaseRegistry(registry_path=str(reg_path), cases_dir=str(cases_dir))

    case_1 = {
        "id": "case-2026-11-01",
        "title": "The Decaf Conspiracy",
        "suspect": {"name": "Penelope Vane"},
        "setting": "City Hall"
    }
    registry.register_case("2026-11-01", case_1, seed_id="crime-02")

    mock_progress = {
        "completed_dates": {
            "2026-11-01": {"won": True}
        }
    }

    archive = registry.get_archive_list(mock_progress)
    assert len(archive) >= 1
    found = next((c for c in archive if c["date"] == "2026-11-01"), None)
    assert found is not None
    assert found["status"] == "SOLVED"
    assert found["won"] is True

def test_registry_recent_constraints(tmp_path):
    reg_path = tmp_path / "case_registry.json"
    cases_dir = tmp_path / "cases"
    registry = CaseRegistry(registry_path=str(reg_path), cases_dir=str(cases_dir))

    registry.register_case("2026-11-01", {"title": "Title 1", "suspect": {"name": "Suspect 1"}}, seed_id="s1")
    registry.register_case("2026-11-02", {"title": "Title 2", "suspect": {"name": "Suspect 2"}}, seed_id="s2")

    titles, suspects = registry.get_recent_suspects_and_titles(limit=5)
    assert "Title 1" in titles
    assert "Title 2" in titles
    assert "Suspect 1" in suspects
    assert "Suspect 2" in suspects

def test_registry_uniqueness_checks(tmp_path):
    reg_path = tmp_path / "case_registry.json"
    cases_dir = tmp_path / "cases"
    registry = CaseRegistry(registry_path=str(reg_path), cases_dir=str(cases_dir))

    registry.register_case("2026-11-01", {"title": "The Sourdough Mystery", "suspect": {"name": "Cornelius Crump"}}, seed_id="crime-06")

    # Collisions
    assert registry.is_case_unique(title="The Sourdough Mystery", suspect_name="Someone Else") is False
    assert registry.is_case_unique(title="Different Title", suspect_name="Cornelius Crump") is False
    assert registry.is_case_unique(title="Different Title", suspect_name="Someone Else", seed_id="crime-06") is False

    # Unique
    assert registry.is_case_unique(title="Brand New Title", suspect_name="Brand New Suspect", seed_id="crime-99") is True

    # Exclude own date
    assert registry.is_case_unique(title="The Sourdough Mystery", suspect_name="Cornelius Crump", seed_id="crime-06", exclude_date="2026-11-01") is True

def test_procedural_case_synthesis(tmp_path):
    from unittest.mock import MagicMock
    from alibi.agents.case_architect import CaseArchitectAgent
    import random

    mock_client = MagicMock()
    reg_path = tmp_path / "case_registry.json"
    cases_dir = tmp_path / "cases"

    agent = CaseArchitectAgent(client=mock_client, cases_dir=str(cases_dir))
    agent.registry.registry_path = str(reg_path)

    seed = {
        "id": "crime-14",
        "title": "The Trophy Case Bowling Ball Swap",
        "description": "The league championship bowling ball was substituted with a hollowed honeydew melon.",
        "setting": "Kingpin Lanes Hall of Fame"
    }

    rng = random.Random(123)
    case = agent._synthesize_unique_case("2026-11-20", seed, rng)

    assert case.title == "The Trophy Case Bowling Ball Swap"
    assert case.date == "2026-11-20"
    assert len(case.dossier) == 3
    assert len(case.truth_timeline) == 3
    assert len(case.lie_plan.weak_points) == 3
    assert len(case.solution_contradictions) == 3
    assert case.suspect.name != ""
    assert case.suspect.quirk != ""


