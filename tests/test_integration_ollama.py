import pytest
import httpx
from alibi.llm.client import OllamaClient

def is_ollama_online():
    try:
        r = httpx.get("http://localhost:11434/api/tags", timeout=2.0)
        return r.status_code == 200
    except Exception:
        return False

@pytest.mark.skipif(not is_ollama_online(), reason="Local Ollama server is not running on localhost:11434")
def test_real_ollama_integration():
    client = OllamaClient()
    connected, msg = client.verify_models()
    assert connected is True, msg

    # Test generation
    prompt = "Respond with JSON containing key 'ping' and value 'pong'."
    res = client.generate_json_with_retry(prompt=prompt, agent_name="TestIntegration")
    assert isinstance(res, dict)
    assert res.get("ping") == "pong" or "ping" in res

    # Test embedding
    emb = client.get_embeddings("The alibi detective test")
    assert len(emb) > 0
    assert isinstance(emb[0], float)
