import json
from typing import Dict, Any, List, Optional, Tuple, Callable
from alibi.models.schema import Case, SuspectResponse, Statement, SuspectToolCall
from alibi.rag.store import RAGStore
from alibi.llm.client import OllamaClient

class SuspectAgent:
    """Agent 2: The core interrogation suspect with hidden reasoning, RAG context, and JSON tool calling."""

    def __init__(self, client: OllamaClient, rag_store: RAGStore):
        self.client = client
        self.rag_store = rag_store
        self.last_tool_calls: List[Dict[str, Any]] = []

    def execute_tool(self, tool_name: str, topic: str, case: Case, transcript: List[Statement]) -> str:
        """Execute one of the four suspect tools."""
        record = {"tool": tool_name, "topic": topic}
        
        if tool_name == "lookup_my_prior_statements":
            # Search prior statements in RAG
            results = self.rag_store.query("statements", topic, top_k=2)
            if results:
                res_str = "\n".join([f"- {r['text']}" for r in results])
            else:
                res_str = "No prior statements recorded on this topic."
            record["result"] = res_str
            self.last_tool_calls.append(record)
            return res_str

        elif tool_name == "lookup_dossier":
            # Search dossier facts in RAG
            results = self.rag_store.query("dossier", topic, top_k=2)
            if results:
                res_str = "\n".join([f"- {r['text']}" for r in results])
            else:
                res_str = "No specific dossier facts found matching topic."
            record["result"] = res_str
            self.last_tool_calls.append(record)
            return res_str

        elif tool_name == "lookup_truth":
            # Search hidden truth timeline in RAG
            results = self.rag_store.query("truth", topic, top_k=2)
            if results:
                res_str = "\n".join([f"- {r['text']}" for r in results])
            else:
                res_str = "No specific truth event found."
            record["result"] = res_str
            self.last_tool_calls.append(record)
            return res_str

        elif tool_name == "plan_lie":
            # Check weak points against question
            q_lower = topic.lower()
            triggered = []
            for wp in case.lie_plan.weak_points:
                for trig in wp.trigger_topics:
                    if trig.lower() in q_lower:
                        triggered.append(wp)
                        break

            if triggered:
                res_str = "APPLICABLE WEAK POINTS DETECTED:\n" + "\n".join([
                    f"- WeakPoint {wp.id}: Claim: '{wp.claim}'. Recommended slip line: '{wp.planned_slip}'"
                    for wp in triggered
                ])
            else:
                res_str = f"No direct weak point hit. General Cover Story: {case.lie_plan.cover_story}"
            record["result"] = res_str
            self.last_tool_calls.append(record)
            return res_str

        res_str = f"Unknown tool: {tool_name}"
        record["result"] = res_str
        self.last_tool_calls.append(record)
        return res_str

    def interrogate(
        self,
        question: str,
        case: Case,
        remaining_tokens: int,
        transcript: List[Statement],
        on_token_callback: Optional[Callable[[str], None]] = None
    ) -> SuspectResponse:
        """Run the suspect response generation with instant tool planning and fast token-bounded LLM response."""
        self.last_tool_calls.clear()

        # Step 1: Pre-retrieve context relevant to the question via RAG
        rag_dossier = self.rag_store.query("dossier", question, top_k=2)
        rag_prior = self.rag_store.query("statements", question, top_k=2)

        # Build initial system prompt
        system_prompt = self._build_system_prompt(case, remaining_tokens)
        
        # Step 2: Instant deterministic tool execution (<0.001s)
        # Checking weak points and cover story in Python avoids a 50s redundant LLM deliberation call
        tool_call_obj = SuspectToolCall(tool="plan_lie", topic=question)
        tool_result = self.execute_tool("plan_lie", question, case, transcript)

        # Step 3: Fast final response generation with num_predict=120 (~3-5s response)
        final_prompt = self._build_final_answer_prompt(
            question=question,
            case=case,
            remaining_tokens=remaining_tokens,
            tool_call=tool_call_obj,
            tool_result=tool_result,
            rag_dossier=rag_dossier,
            rag_prior=rag_prior
        )

        try:
            final_json = self.client.generate_json_with_retry(
                prompt=final_prompt,
                system=system_prompt,
                temperature=0.7,
                schema_cls=SuspectResponse,
                agent_name="SuspectAgent",
                num_predict=120,
                max_retries=1
            )
            resp = SuspectResponse.model_validate(final_json)
        except Exception:
            # Fallback in case of strict JSON parsing issue
            emotion = "panicked" if remaining_tokens <= 1 else ("nervous" if remaining_tokens <= 3 else "defensive")
            # If question matches a weak point, use the planned slip!
            matched_slip = None
            q_low = question.lower()
            for wp in case.lie_plan.weak_points:
                if any(t.lower() in q_low for t in wp.trigger_topics):
                    matched_slip = wp.planned_slip
                    break
            spoken = matched_slip or f"I have already told you, detective: {case.lie_plan.cover_story[:100]}!"
            resp = SuspectResponse(
                inner_reasoning="Model generation recovered via fallback strategy.",
                spoken_answer=spoken,
                emotion=emotion
            )

        if on_token_callback:
            # Deliver spoken words to typewriter UI
            on_token_callback(resp.spoken_answer)

        return resp

    def _build_system_prompt(self, case: Case, remaining_tokens: int) -> str:
        emotion_guide = "smug or calm" if remaining_tokens >= 4 else ("nervous or defensive" if remaining_tokens >= 2 else "panicked")
        return (
            f"You are roleplaying as {case.suspect.name}, a {case.suspect.occupation}.\n"
            f"SPEECH QUIRK: {case.suspect.quirk}\n"
            f"YOU ARE GUILTY of the crime: '{case.crime_description}'.\n"
            f"CRITICAL BEHAVIOR RULES:\n"
            f"1. You desperately want to avoid being caught. NEVER confess or admit guilt.\n"
            f"2. You MUST stay in character with your speech quirk at all times.\n"
            f"3. Keep your spoken_answer concise: strictly UNDER 60 words.\n"
            f"4. You are a flawed liar. When pressed on your weak points, you may slip or present your planned lie line.\n"
            f"5. Current pressure level: Remaining detective tokens: {remaining_tokens}/5. Your emotion should be {emotion_guide}.\n"
            f"6. Never reveal your inner reasoning in your spoken answer."
        )

    def _build_deliberation_prompt(self, question: str, case: Case, remaining_tokens: int, rag_dossier: List[Dict], rag_prior: List[Dict]) -> str:
        return (
            f"The detective asks: \"{question}\"\n"
            f"Case Cover Story: {case.lie_plan.cover_story}\n"
            f"Retrieved Dossier Context: {[d['text'] for d in rag_dossier]}\n"
            f"Retrieved Prior Statements: {[p['text'] for p in rag_prior]}\n\n"
            f"Choose whether to call a tool before answering:\n"
            f"Tools available:\n"
            f"- 'plan_lie' (topic: question string)\n"
            f"- 'lookup_my_prior_statements' (topic: search keywords)\n"
            f"- 'lookup_dossier' (topic: search keywords)\n"
            f"- 'lookup_truth' (topic: search keywords)\n\n"
            f"Output JSON:\n"
            f"{{\n"
            f'  "tool_call": {{"tool": "plan_lie", "topic": "{question}"}}\n'
            f"}}"
        )

    def _build_final_answer_prompt(
        self,
        question: str,
        case: Case,
        remaining_tokens: int,
        tool_call: Optional[SuspectToolCall],
        tool_result: Optional[str],
        rag_dossier: List[Dict],
        rag_prior: List[Dict]
    ) -> str:
        prompt = (
            f"Detective Question: \"{question}\"\n"
            f"Your General Cover Story: {case.lie_plan.cover_story}\n"
            f"Retrieved Dossier Facts: {[d['text'] for d in rag_dossier]}\n"
            f"Retrieved Prior Statements: {[p['text'] for p in rag_prior]}\n"
        )
        if tool_call and tool_result:
            prompt += f"\nTool Execution [{tool_call.tool}]:\n{tool_result}\n"

        prompt += (
            f"\nSLIP MECHANIC: If the tool result or question touches a planned weak point, deliver the planned cover-story line or slip!\n"
            f"Ensure spoken_answer is under 60 words and embodies your quirk: {case.suspect.quirk}\n\n"
            f"Output JSON with fields:\n"
            f"{{\n"
            f'  "inner_reasoning": "Private thoughts analyzing the danger and strategy",\n'
            f'  "spoken_answer": "In-character reply spoken out loud to detective (under 60 words)",\n'
            f'  "emotion": "calm|nervous|defensive|smug|panicked"\n'
            f"}}"
        )
        return prompt
