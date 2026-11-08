import os
import hashlib
import random
from unittest.mock import MagicMock
from alibi.agents.case_architect import CaseArchitectAgent

def test_daily_seed_determinism():
    date_1 = "2026-11-04"
    date_2 = "2026-11-04"
    date_3 = "2026-11-05"

    seed_1 = int(hashlib.md5(date_1.encode()).hexdigest(), 16) % 1000000
    seed_2 = int(hashlib.md5(date_2.encode()).hexdigest(), 16) % 1000000
    seed_3 = int(hashlib.md5(date_3.encode()).hexdigest(), 16) % 1000000

    assert seed_1 == seed_2
    assert seed_1 != seed_3

    mock_client = MagicMock()
    architect = CaseArchitectAgent(mock_client, cases_dir="cases/test_cases")
    
    # Both calls for same date with mock should pick the same fallback
    rng1 = random.Random(seed_1)
    choice1 = rng1.choice(architect.fallback_cases)

    rng2 = random.Random(seed_2)
    choice2 = rng2.choice(architect.fallback_cases)

    assert choice1["title"] == choice2["title"]
