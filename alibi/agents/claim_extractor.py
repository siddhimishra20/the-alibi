import re
from typing import List, Dict, Any
from alibi.models.schema import AtomicClaim, ExtractedClaimsResponse
from alibi.llm.client import OllamaClient
from alibi.rag.store import RAGStore

class ClaimExtractorAgent:
    """Agent 3: Extracts structured atomic claims from suspect responses and indexes them into RAG."""

    def __init__(self, client: OllamaClient, rag_store: RAGStore):
        self.client = client
        self.rag_store = rag_store

    def extract_and_store(self, turn_number: int, spoken_answer: str, use_llm: bool = False) -> List[AtomicClaim]:
        """Extract atomic claims and commit them to the vector store and ledger.
        
        Uses ultra-fast linguistic clause decomposition (0.0001s) by default,
        with optional LLM fallback to preserve sub-second response times.
        """
        claims: List[AtomicClaim] = []

        if not use_llm:
            # High-speed deterministic extraction: splits into atomic propositions & extracts temporal markers
            sentences = [s.strip() for s in re.split(r'[.!?;]+', spoken_answer) if len(s.strip()) > 3]
            for s in sentences[:3]:
                # Extract time if present
                time_match = re.search(r'\b(?:\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm)|\d{1,2}\s*o\'clock|noon|midnight)\b', s, re.IGNORECASE)
                time_str = time_match.group(0) if time_match else None

                # Extract location prepositional phrase if present
                place_match = re.search(r'\b(?:at|in|near|inside|behind)\s+the\s+([A-Za-z\s]+?)(?:,|$|\.|\sat|\sin)', s, re.IGNORECASE)
                place_str = place_match.group(1).strip() if place_match else None

                claims.append(AtomicClaim(
                    subject="Suspect",
                    predicate="stated",
                    object=s[:120],
                    time=time_str,
                    place=place_str
                ))
        else:
            system_prompt = (
                "You are a Forensic Linguistic Claim Extractor.\n"
                "Your task is to break down the suspect's spoken sentence into 1 to 3 atomic factual claims.\n"
                "Output strictly JSON adhering to the schema."
            )
            user_prompt = (
                f"Extract atomic claims from this statement:\n"
                f"\"{spoken_answer}\"\n\n"
                f"Output format:\n"
                f"{{\n"
                f'  "claims": [\n'
                f'    {{"subject": "...", "predicate": "...", "time": "...", "place": "...", "object": "..."}}\n'
                f'  ]\n'
                f"}}"
            )
            try:
                data = self.client.generate_json_with_retry(
                    prompt=user_prompt,
                    system=system_prompt,
                    temperature=0.1,
                    schema_cls=ExtractedClaimsResponse,
                    agent_name="ClaimExtractor",
                    num_predict=80,
                    max_retries=1
                )
                for c in data.get("claims", []):
                    claims.append(AtomicClaim(**c))
            except Exception:
                claims.append(AtomicClaim(
                    subject="Suspect",
                    predicate="stated",
                    object=spoken_answer[:80]
                ))

        if not claims:
            claims.append(AtomicClaim(
                subject="Suspect",
                predicate="stated",
                object=spoken_answer[:80]
            ))

        # Store in RAG vector store
        try:
            self.rag_store.add_suspect_statement(turn=turn_number, answer=spoken_answer, claims=claims)
        except Exception:
            pass

        return claims
