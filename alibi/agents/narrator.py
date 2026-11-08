import random
from typing import Optional
from alibi.models.schema import Case
from alibi.llm.client import OllamaClient

class NarratorAgent:
    """Agent 5: Noir-style narrator providing introductory briefings, commentary, and cryptic hints."""

    def __init__(self, client: OllamaClient):
        self.client = client

    def get_briefing_narration(self, case: Case) -> str:
        """Introductory briefing narration set in the scene."""
        prompt = (
            f"Write a 2-3 sentence gritty, atmospheric noir detective introduction for this case:\n"
            f"Title: {case.title}\n"
            f"Setting: {case.setting}\n"
            f"Crime: {case.crime_description}\n"
            f"Suspect: {case.suspect.name}, {case.suspect.occupation}\n"
            f"Style: 1940s hardboiled detective monologue with rain on windowpanes and cheap coffee."
        )
        try:
            return self.client.generate(prompt=prompt, temperature=0.7, agent_name="NarratorBriefing", num_predict=75).strip()
        except Exception:
            return (
                f"Rain drummed against the Venetian blinds like a cheap snare drum. "
                f"Word came down from {case.setting}: {case.crime_description}. "
                f"And sitting across from me was {case.suspect.name}, looking as guilty as a cat in a canary cage."
            )

    def generate_hint(self, case: Case) -> str:
        """Provide a subtle noir hint nudging toward an unexposed weak point without spoiling the exact solution."""
        if not case.lie_plan.weak_points:
            return "Check the times and places carefully, detective. Liars always trip over their own clocks."

        # Pick one weak point
        wp = random.choice(case.lie_plan.weak_points)
        topics = ", ".join(wp.trigger_topics[:3])

        prompt = (
            f"You are a noir narrator whispering a cryptic clue to a detective.\n"
            f"The suspect has a vulnerability regarding: {topics}.\n"
            f"Their cover story is: {case.lie_plan.cover_story}\n"
            f"Write ONE atmospheric noir hint sentence that directs the detective's curiosity toward {topics} without giving away the exact answer."
        )

        try:
            hint = self.client.generate(prompt=prompt, temperature=0.7, agent_name="NarratorHint", num_predict=50).strip()
            return hint.replace('"', '')
        except Exception:
            return f"Keep your eyes on the details around {topics}. Something smells fishier than a harbor fishmonger."
