import json
import pytest
from alibi.llm.client import OllamaClient

def test_clean_json_code_fences():
    client = OllamaClient()
    raw = "```json\n{\n  \"status\": \"ok\",\n  \"count\": 42\n}\n```"
    cleaned = client.clean_json_text(raw)
    parsed = json.loads(cleaned)
    assert parsed["status"] == "ok"
    assert parsed["count"] == 42

def test_clean_json_preamble_and_postamble():
    client = OllamaClient()
    raw = "Here is the requested output:\n\n{\"verdict\": \"VALID\"}\n\nHope this helps!"
    cleaned = client.clean_json_text(raw)
    parsed = json.loads(cleaned)
    assert parsed["verdict"] == "VALID"

def test_clean_json_trailing_commas():
    client = OllamaClient()
    raw = "{\"items\": [1, 2, 3, ], \"valid\": true, }"
    cleaned = client.clean_json_text(raw)
    parsed = json.loads(cleaned)
    assert parsed["valid"] is True
    assert len(parsed["items"]) == 3
