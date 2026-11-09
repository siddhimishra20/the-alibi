import json
from typing import Dict, Any, Optional, List, Tuple
from alibi.models.schema import Case, AccusationResult, JudgeEvaluation
from alibi.rag.store import RAGStore
from alibi.llm.client import OllamaClient

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "up", "about", "into", "over", "after",
    "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "i", "you", "he", "she", "it", "we", "they",
    "my", "your", "his", "her", "its", "our", "their", "this", "that",
    "these", "those", "am", "so", "as", "if", "not", "no", "just", "then",
    "there", "here", "when", "where", "why", "how", "all", "any", "both"
}

class ContradictionJudgeAgent:
    """Agent 4: Evaluates accusations using Chain of Verification and strict mutual-exclusivity standards."""

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
        """Run strict contradiction verification using LLM Chain of Verification with deterministic fallback."""
        # Retrieve RAG context surrounding the target and quote
        rag_context = self.rag_store.query("dossier", f"{quote} {target_text}", top_k=2)
        context_snippets = [r["text"] for r in rag_context] if rag_context else []

        prompt = (
            f"CRITICAL LEGAL DIRECTIVE: You are an exceptionally strict, unbribable Contradiction Judge in a hardboiled detective courtroom.\n"
            f"Your sole job is to test if the Detective has proven a DIRECT, AIRTIGHT, MUTUALLY EXCLUSIVE CONTRADICTION between the Suspect's Quote and the Target Fact/Statement.\n\n"
            f"STANDARD OF PROOF (HIGH):\n"
            f"1. MUTUAL EXCLUSIVITY: Claim A and Claim B CANNOT BOTH BE TRUE in the real physical universe.\n"
            f"2. SAME TOPIC: Both statements must be about the exact same entity, time, location, or physical condition.\n"
            f"3. NO SPECULATION: You must NEVER assume hidden facts. If Claim A and Claim B can both be true simultaneously (even if suspicious), you MUST rule INVALID.\n"
            f"4. CIRCUMSTANTIAL != CONTRADICTION: An alibi like 'I was drinking tea' does NOT contradict 'Yarn was found on a bird' (both can be true).\n"
            f"5. DEFAULT TO INVALID: Unless the suspect explicitly asserted something that is physically or factually impossible given the target fact, rule INVALID.\n\n"
            f"PRECEDENTS:\n"
            f"- Quote: \"I was drinking tea in my parlor.\" vs Fact: \"Green yarn was found on the stolen flamingo.\"\n"
            f"  Verdict: INVALID. Reason: A suspect drinking tea does not deny owning green yarn. Both can co-exist.\n"
            f"- Quote: \"I walked past the hardware store at dusk.\" vs Fact: \"Receipt for wire cutters at 6:30 PM.\"\n"
            f"  Verdict: INVALID. Reason: Walking past a store does not contradict a receipt without an explicit denial of purchasing.\n"
            f"- Quote: \"I have never touched or owned emerald Shetland yarn in my entire life.\" vs Fact: \"Strands of emerald Shetland yarn were found at the crime scene.\"\n"
            f"  Verdict: VALID. Reason: The suspect's absolute denial of ever possessing this specific yarn directly conflicts with the physical evidence.\n"
            f"- Quote: \"The sky was bone dry and cloudless all night.\" vs Fact: \"Torrential rainstorm from midnight to 3 AM.\"\n"
            f"  Verdict: VALID. Reason: A cloudless, dry night is physically incompatible with a recorded torrential rainstorm.\n\n"
            f"CASE UNDER TRIAL:\n"
            f"Suspect Quote: \"{quote}\"\n"
            f"Target {'Dossier Fact' if is_dossier_fact else 'Prior Statement'}: \"{target_text}\"\n"
            f"Case Crime: {case.crime_description}\n"
            f"Forensic Context: {context_snippets}\n\n"
            f"Chain of Verification:\n"
            f"1. Exactly what does the suspect assert?\n"
            f"2. Exactly what does the target fact prove?\n"
            f"3. Could both possibly be true at the same time without violating the laws of physics or logic?\n"
            f"4. Verdict: If they could coexist or discuss different topics -> INVALID. Only if strictly mutually exclusive -> VALID.\n"
            f"5. Narration: One hardboiled sentence delivering the verdict in the voice of a dry noir narrator.\n\n"
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
            "You are an exceptionally strict, impartial Contradiction Judge in a hardboiled noir courtroom.\n"
            "Default to INVALID. Rule VALID only if the suspect's quote and the target fact are directly mutually exclusive and physically cannot coexist."
        )

        final_verdict = "INVALID"
        explanation = "The court finds no direct, mutually exclusive contradiction between the statement and the evidence."

        try:
            res = self.client.generate_json_with_retry(
                prompt=prompt,
                system=system_prompt,
                temperature=0.05,
                schema_cls=JudgeEvaluation,
                agent_name="JudgeEval",
                num_predict=250,
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

    def _deterministic_contradiction_check(self, quote: str, target: str, case: Case) -> Tuple[str, str]:
        """Strict deterministic fallback when LLM is unavailable."""
        q_words = set(quote.lower().split()) - STOPWORDS
        t_words = set(target.lower().split()) - STOPWORDS
        t_lower = target.lower()

        # Check against planned weak points
        for wp in case.lie_plan.weak_points:
            slip_words = set(wp.planned_slip.lower().split()) - STOPWORDS
            overlap = len(slip_words.intersection(q_words))
            claim_match = len(wp.claim) > 10 and wp.claim.lower() in quote.lower()

            if overlap >= 4 or claim_match:
                # Must match the specific conflicting dossier fact
                for fact in case.dossier:
                    if fact.id == wp.conflicts_with:
                        fact_words = set(fact.text.lower().split()) - STOPWORDS
                        if fact.id.lower() in t_lower or len(fact_words.intersection(t_words)) >= 4:
                            return "VALID", f"The suspect's claim directly contradicts {fact.id}: the facts don't lie, but the suspect certainly did."

        # Check solution contradictions with strict high-overlap requirement
        for sol in case.solution_contradictions:
            sol_words = set(sol.lower().split()) - STOPWORDS
            q_overlap = len(sol_words.intersection(q_words))
            t_overlap = len(sol_words.intersection(t_words))
            if q_overlap >= 4 and t_overlap >= 4:
                return "VALID", "A textbook contradiction caught dead to rights. The story collapses like a house of cards."

        return "INVALID", "The court finds no direct, mutually exclusive contradiction between the statement and the evidence."

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
