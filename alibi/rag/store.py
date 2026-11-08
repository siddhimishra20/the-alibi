import os
import re
from typing import List, Dict, Any, Optional
import numpy as np
import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

from alibi.models.schema import VerifiedFact, TimelineEvent, AtomicClaim
from alibi.llm.client import OllamaClient

class OllamaEmbeddingFunction(EmbeddingFunction):
    """Bridge Ollama nomic-embed-text to ChromaDB."""
    def __init__(self, client: Optional[OllamaClient] = None):
        self.client = client or OllamaClient()

    @staticmethod
    def name() -> str:
        return "ollama_nomic_embed"

    def get_config(self) -> dict:
        url = getattr(self.client, "base_url", None)
        return {"base_url": url if isinstance(url, str) else "http://localhost:11434"}

    @classmethod
    def build_from_config(cls, config: dict):
        return cls(client=OllamaClient(base_url=config.get("base_url", "http://localhost:11434")))


    def __call__(self, input: Documents) -> Embeddings:
        results = []
        for doc in input:
            emb = self.client.get_embeddings(doc)
            if not emb:
                # Fallback to zero vector if embedding fails
                emb = [0.0] * 768
            results.append(emb)
        return results

class RAGStore:
    """Manages three distinct vector collections per game session with hybrid keyword reranking."""

    def __init__(self, session_id: str, client: OllamaClient, persist_dir: str = "data/chroma_db"):
        self.session_id = session_id.replace("-", "_")
        self.client = client
        self.persist_dir = persist_dir
        os.makedirs(self.persist_dir, exist_ok=True)
        
        self.embed_fn = OllamaEmbeddingFunction(client)
        self.chroma_client = chromadb.PersistentClient(path=self.persist_dir)
        
        # 3 collections per session
        self.col_dossier_name = f"dossier_{self.session_id}"
        self.col_truth_name = f"truth_{self.session_id}"
        self.col_statements_name = f"statements_{self.session_id}"

        # Clean/reset collections for new session if already existing
        self._init_collections()
        self.last_retrievals: List[Dict[str, Any]] = []

    def _init_collections(self):
        try:
            self.dossier_col = self.chroma_client.get_or_create_collection(
                name=self.col_dossier_name,
                embedding_function=self.embed_fn
            )
            self.truth_col = self.chroma_client.get_or_create_collection(
                name=self.col_truth_name,
                embedding_function=self.embed_fn
            )
            self.statements_col = self.chroma_client.get_or_create_collection(
                name=self.col_statements_name,
                embedding_function=self.embed_fn
            )
        except Exception:
            # Fallback if names conflict
            self.dossier_col = self.chroma_client.create_collection(
                name=f"{self.col_dossier_name}_alt",
                embedding_function=self.embed_fn
            )
            self.truth_col = self.chroma_client.create_collection(
                name=f"{self.col_truth_name}_alt",
                embedding_function=self.embed_fn
            )
            self.statements_col = self.chroma_client.create_collection(
                name=f"{self.col_statements_name}_alt",
                embedding_function=self.embed_fn
            )

    def populate_dossier(self, facts: List[VerifiedFact]):
        """Index verified facts."""
        if not facts:
            return
        docs = [f"Fact {f.id}: {f.text}" for f in facts]
        ids = [f.id for f in facts]
        metas = [{"fact_id": f.id, "type": "dossier"} for f in facts]
        self.dossier_col.upsert(documents=docs, ids=ids, metadatas=metas)

    def populate_truth_timeline(self, timeline: List[TimelineEvent]):
        """Index hidden truth timeline."""
        if not timeline:
            return
        docs = [f"[{e.time}] {e.event}" for e in timeline]
        ids = [f"truth_{i}" for i in range(len(timeline))]
        metas = [{"time": e.time, "type": "truth"} for e in timeline]
        self.truth_col.upsert(documents=docs, ids=ids, metadatas=metas)

    def add_suspect_statement(self, turn: int, answer: str, claims: List[AtomicClaim]):
        """Index suspect's spoken statement and atomic claims."""
        # Main spoken answer
        doc_main = f"Turn {turn} Statement: {answer}"
        id_main = f"stmt_turn_{turn}"
        meta_main = {"turn": turn, "type": "statement_full"}
        
        docs = [doc_main]
        ids = [id_main]
        metas = [meta_main]

        # Sub-claims
        for i, c in enumerate(claims):
            c_text = f"Turn {turn} Claim: {c.subject} {c.predicate} {c.object or ''} {f'at {c.time}' if c.time else ''} {f'in {c.place}' if c.place else ''}".strip()
            docs.append(c_text)
            ids.append(f"stmt_turn_{turn}_claim_{i}")
            metas.append({"turn": turn, "type": "statement_claim", "subject": c.subject, "predicate": c.predicate})

        self.statements_col.upsert(documents=docs, ids=ids, metadatas=metas)

    def _keyword_boost(self, query: str, document: str) -> float:
        """Calculate simple token overlap bonus (0.0 to 0.5)."""
        q_words = set(re.findall(r'\w+', query.lower()))
        if not q_words:
            return 0.0
        doc_words = set(re.findall(r'\w+', document.lower()))
        overlap = len(q_words.intersection(doc_words))
        return min(0.5, (overlap / len(q_words)) * 0.5)

    def query(self, collection_name: str, query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Retrieve top-k documents with hybrid semantic + keyword reranking."""
        target_col = None
        if "dossier" in collection_name.lower():
            target_col = self.dossier_col
        elif "truth" in collection_name.lower():
            target_col = self.truth_col
        else:
            target_col = self.statements_col

        count = target_col.count()
        if count == 0:
            return []

        candidate_k = min(count, max(top_k * 3, 10))
        results = target_col.query(query_texts=[query_text], n_results=candidate_k)
        
        docs = results.get("documents", [[]])[0]
        distances = results.get("distances", [[]])[0] if results.get("distances") else [0.0] * len(docs)
        metas = results.get("metadatas", [[]])[0]
        ids = results.get("ids", [[]])[0]

        scored_items = []
        for doc_text, dist, meta, item_id in zip(docs, distances, metas, ids):
            # Chroma distance is L2 by default; approximate similarity
            base_score = 1.0 / (1.0 + float(dist)) if dist is not None else 0.5
            boost = self._keyword_boost(query_text, doc_text)
            final_score = base_score + boost
            scored_items.append({
                "id": item_id,
                "text": doc_text,
                "score": round(final_score, 3),
                "metadata": meta,
                "collection": collection_name
            })

        # Sort by reranked score
        scored_items.sort(key=lambda x: x["score"], reverse=True)
        final_top = scored_items[:top_k]

        # Record in retrieval history for debug panel
        self.last_retrievals.append({
            "query": query_text,
            "collection": collection_name,
            "results": final_top
        })
        return final_top
