import json
from typing import Dict, Any, Optional, List
from alibi.models.schema import Case, AccusationResult, JudgeEvaluation
from alibi.rag.store import RAGStore
from alibi.llm.client import OllamaClient

class ContradictionJudgeAgent:
    """Agent 4: Evaluates accusations using Chain of Verification, self-consistency check, and deterministic fallback."""

    def __init__(self, client: OllamaClient, rag_store: RAGStore):
        self.client = client
        self.rag_store = rag_store

    def judge_accusation(
        self,
        quote: str,
        target_text: str,
        case: Case,
        is_dossier_fact: bool = True
    ) -> AccusationResult:
        """Run fast contradiction verification with deterministic pre-check and single-pass judge evaluation."""
        # 1. Deterministic instant pre-check: if it directly matches a planned weak point or solution contradiction,
        # return immediately (0.001s response time)
        det_verdict, det_exp = self._deterministic_contradiction_check(quote, target_text, case)
        if det_verdict == "VALID":
            breakdown = self.generate_confession_breakdown(case, quote, target_text)
            return AccusationResult(
                valid=True,
                verdict="VALID",
                explanation=det_exp,
                highlighted_quote=quote,
                target_text=target_text,
                breakdown_confession=breakdown
            )

        # 2. Retrieve RAG context surrounding the target and quote
        rag_context = self.rag_store.query("dossier", f"{quote} {target_text}", top_k=2)

        prompt = (
            f"EVALUATE CONTRADICTION:\n"
            f"Suspect's Highlighted Quote: \"{quote}\"\n"
            f"Target {'Dossier Fact' if is_dossier_fact else 'Prior Statement'}: \"{target_text}\"\n"
            f"Retrieved Forensic Context: {[r['text'] for r in rag_context]}\n\n"
            f"Chain of Verification Procedure:\n"
            f"Step 1: Restate claim A (from the quote) neutrally and objectively.\n"
            f"Step 2: Restate claim B (from the target) neutrally and objectively.\n"
            f"Step 3: Logical incompatibility check: Can Claim A and Claim B both be true in reality, or do they mutually exclude each other?\n"
            f"Step 4: Verdict: VALID if they are clearly incompatible, INVALID if they could coexist or are irrelevant.\n"
            f"Step 5: Provide a one-sentence explanation in the voice of a dry, hardboiled noir narrator.\n\n"
            f"Output strictly JSON with format:\n"
            f"{{\n"
            f'  "claim_a_neutral": "...",\n'
            f'  "claim_b_neutral": "...",\n'
            f'  "logical_incompatibility": "...",\n'
            f'  "verdict": "VALID|INVALID",\n'
            f'  "narration": "..."\n'
            f"}}"
        )

        system_prompt = (
            "You are an impartial Contradiction Judge and dry noir narrator.\n"
            "You determine whether a suspect's statement logically contradicts known facts or earlier testimony.\n"
            "Be strict and precise: a valid contradiction means both claims cannot simultaneously be true."
        )

        final_verdict = "INVALID"
        explanation = "The claims do not present an irreconcilable logical clash."

        try:
            res = self.client.generate_json_with_retry(
                prompt=prompt,
                system=system_prompt,
                temperature=0.1,
                schema_cls=JudgeEvaluation,
                agent_name="JudgeEval",
                num_predict=130,
                max_retries=1
            )
            eval_obj = JudgeEvaluation.model_validate(res)
            final_verdict = eval_obj.verdict
            if eval_obj.narration:
                explanation = eval_obj.narration
        except Exception:
            final_verdict, explanation = self._deterministic_contradiction_check(quote, target_text, case)

        is_valid = (final_verdict == "VALID")
        breakdown = None
        if is_valid:
            breakdown = self.generate_confession_breakdown(case, quote, target_text)

        return AccusationResult(
            valid=is_valid,
            verdict="VALID" if is_valid else "INVALID",
            explanation=explanation,
            highlighted_quote=quote,
            target_text=target_text,
            breakdown_confession=breakdown
        )

    def _deterministic_contradiction_check(self, quote: str, target: str, case: Case) -> (str, str):
        """Deterministic keyword and weak point overlap fallback."""
        q_lower = quote.lower()
        t_lower = target.lower()

        # Check against planned weak points
        for wp in case.lie_plan.weak_points:
            # Check if quote matches planned slip or claim
            slip_words = set(wp.planned_slip.lower().split())
            quote_words = set(q_lower.split())
            overlap = len(slip_words.intersection(quote_words))
            
            if overlap >= 3 or wp.claim.lower() in q_lower:
                # Find matching target
                for fact in case.dossier:
                    if fact.id == wp.conflicts_with and (fact.text.lower() in t_lower or fact.id in t_lower):
                        return "VALID", f"The suspect's claim directly contradicts {fact.id}: the facts don't lie, but the suspect certainly did."

        # Check solution contradictions
        for sol in case.solution_contradictions:
            words = set(sol.lower().split())
            if len(words.intersection(set(q_lower.split()))) >= 2 and len(words.intersection(set(t_lower.split()))) >= 2:
                return "VALID", "A textbook contradiction caught dead to rights. The story collapses like a house of cards."

        return "INVALID", "Close, but the pieces don't definitively lock together as a lie."

    def generate_confession_breakdown(self, case: Case, quote: str, target: str) -> str:
        """Generate suspect's dramatic in-character breakdown upon being cornered."""
        system_prompt = (
            f"You are {case.suspect.name}, the guilty suspect.\n"
            f"SPEECH QUIRK: {case.suspect.quirk}\n"
            f"You were just caught in an undeniable contradiction! The detective cornered you!\n"
            f"Write a dramatic, hilarious, 2-to-3 sentence confession admitting the micro-crime while fully maintaining your speech quirk."
        )
        user_prompt = (
            f"You claimed: \"{quote}\"\n"
            f"Which contradicted: \"{target}\"\n"
            f"Crime: {case.crime_description}\n"
            f"Confess dramatically in character!"
        )

        try:
            return self.client.generate(
                prompt=user_prompt,
                system=system_prompt,
                temperature=0.8,
                agent_name="SuspectConfession",
                num_predict=90
            ).strip()
        except Exception:
            return f"Curse it all! You caught me red-handed! Yes, I did it—{case.crime_description}!"
