import os
import pytest
from unittest.mock import MagicMock
from alibi.rag.store import RAGStore
from alibi.models.schema import VerifiedFact, TimelineEvent, AtomicClaim

def test_rag_store_indexing_and_reranking():
    mock_client = MagicMock()
    # Mock embeddings return non-zero vector
    mock_client.get_embeddings.return_value = [0.05] * 768

    rag = RAGStore(session_id="test_rag_session", client=mock_client, persist_dir="data/test_chroma")
    
    facts = [
        VerifiedFact(id="fact-1", text="Canary-yellow boots were seen in the hall."),
        VerifiedFact(id="fact-2", text="Power was abruptly cut at 11:15 PM."),
        VerifiedFact(id="fact-3", text="Spork Emporium receipt recovered from bin.")
    ]
    rag.populate_dossier(facts)

    # Keyword overlap boost test
    boost = rag._keyword_boost("boots", "Canary-yellow boots were seen")
    assert boost > 0.0

    # Query
    results = rag.query("dossier", "yellow boots", top_k=2)
    assert len(results) > 0
    assert any("boots" in r["text"].lower() for r in results)
