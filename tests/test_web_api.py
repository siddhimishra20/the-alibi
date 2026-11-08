from fastapi.testclient import TestClient
from alibi.server import app

client = TestClient(app)

def test_api_status():
    resp = client.get("/api/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert data["status"] == "online"
    assert "today" in data

def test_api_today_case_sanitized():
    resp = client.get("/api/case/today")
    assert resp.status_code == 200
    data = resp.json()
    assert "id" in data
    assert "title" in data
    assert "dossier" in data
    assert len(data["dossier"]) == 3
    assert "suspect" in data
    # Ensure spoilers are hidden from player
    assert "truth_timeline" not in data
    assert "lie_plan" not in data
    assert "solution_contradictions" not in data

def test_api_archive_listing():
    resp = client.get("/api/archive")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 7

def test_api_session_start_and_interrogate():
    # Start practice session on classic difficulty
    resp = client.post("/api/session/start", json={"practice": True, "difficulty": "classic"})
    assert resp.status_code == 200
    session_data = resp.json()
    assert "session_id" in session_data
    assert session_data["remaining_tokens"] == 5

    sess_id = session_data["session_id"]

    # Interrogate
    q_resp = client.post("/api/session/interrogate", json={
        "session_id": sess_id,
        "question": "Where were you at 10 PM?"
    })
    assert q_resp.status_code == 200
    interrogate_data = q_resp.json()
    assert interrogate_data["success"] is True
    assert "answer" in interrogate_data
    assert interrogate_data["remaining_tokens"] == 4

def test_api_session_difficulty_tokens():
    # Hardboiled = 3 tokens
    hb_resp = client.post("/api/session/start", json={"practice": True, "difficulty": "hardboiled"})
    assert hb_resp.status_code == 200
    assert hb_resp.json()["remaining_tokens"] == 3

    # Rookie = 7 tokens
    rk_resp = client.post("/api/session/start", json={"practice": True, "difficulty": "rookie"})
    assert rk_resp.status_code == 200
    assert rk_resp.json()["remaining_tokens"] == 7

