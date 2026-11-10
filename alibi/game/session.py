import os
import json
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple

from alibi.models.schema import Case, GameSession, Statement, AtomicClaim, AccusationResult
from alibi.llm.client import OllamaClient
from alibi.rag.store import RAGStore
from alibi.agents.suspect import SuspectAgent
from alibi.agents.claim_extractor import ClaimExtractorAgent
from alibi.agents.judge import ContradictionJudgeAgent
from alibi.agents.narrator import NarratorAgent
from alibi.audio.manager import AudioManager
from alibi.game.scoring import calculate_score, get_detective_rank

class GameManager:
    """Orchestrates game state, token accounting, agent pipeline, and daily save persistence."""

    def __init__(self, client: OllamaClient, saves_path: Optional[str] = None):
        self.client = client
        if saves_path is None:
            saves_path = "/tmp/saves/progress.json" if os.getenv("VERCEL") else "saves/progress.json"
        self.saves_path = saves_path
        self.audio = AudioManager.get_instance()
        os.makedirs(os.path.dirname(self.saves_path), exist_ok=True)
        self.session: Optional[GameSession] = None
        self.rag_store: Optional[RAGStore] = None
        self.suspect_agent: Optional[SuspectAgent] = None
        self.claim_extractor: Optional[ClaimExtractorAgent] = None
        self.judge_agent: Optional[ContradictionJudgeAgent] = None
        self.narrator_agent = NarratorAgent(client)
        self.last_score_info: Optional[Dict[str, Any]] = None
        self.progress_data = self._load_progress()

    def _load_progress(self) -> Dict[str, Any]:
        if os.path.exists(self.saves_path):
            try:
                with open(self.saves_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "total_score" not in data:
                        data["total_score"] = 0
                    if "high_score" not in data:
                        data["high_score"] = 0
                    # Backfill any existing wins that lack score breakdown
                    migrated = False
                    for d_key, c_entry in data.get("completed_dates", {}).items():
                        if c_entry.get("won") and "score" not in c_entry:
                            toks = c_entry.get("tokens_left", 3)
                            turns = c_entry.get("turns_taken", 1)
                            sc = calculate_score(
                                won=True,
                                remaining_tokens=toks,
                                turns_taken=turns,
                                hint_used=False,
                                difficulty="classic",
                                streak=1
                            )
                            c_entry["score"] = sc["total"]
                            c_entry["score_breakdown"] = sc
                            data["total_score"] += sc["total"]
                            if sc["total"] > data["high_score"]:
                                data["high_score"] = sc["total"]
                            migrated = True
                    if migrated:
                        self.progress_data = data
                        self._save_progress()
                    return data
            except Exception:
                pass
        return {
            "completed_dates": {},
            "games_played": 0,
            "games_won": 0,
            "current_streak": 0,
            "max_streak": 0,
            "total_score": 0,
            "high_score": 0,
            "last_played_date": None
        }

    def _save_progress(self):
        try:
            with open(self.saves_path, "w", encoding="utf-8") as f:
                json.dump(self.progress_data, f, indent=2)
        except Exception:
            pass

    def reload_progress(self) -> Dict[str, Any]:
        """Reload progress data fresh from disk."""
        self.progress_data = self._load_progress()
        return self.progress_data

    def is_daily_completed(self, date_str: str) -> bool:
        """Check if today's case was already completed."""
        self.reload_progress()
        return date_str in self.progress_data.get("completed_dates", {})

    def get_completed_result(self, date_str: str) -> Optional[Dict[str, Any]]:
        self.reload_progress()
        return self.progress_data.get("completed_dates", {}).get(date_str)

    def init_session(self, case: Case, is_practice: bool = False, difficulty: str = "classic"):
        """Initialize session, RAG vector store collections, and agent dependencies (with mid-game resume support)."""
        self.is_practice = is_practice
        self.difficulty = difficulty
        max_tok = 3 if difficulty == "hardboiled" else (7 if difficulty == "rookie" else 5)
        session_id = f"{case.date}_{int(time.time())}" if is_practice else f"{case.date}"

        # Initialize RAG store with case collections
        self.rag_store = RAGStore(session_id=session_id, client=self.client)
        self.rag_store.populate_dossier(case.dossier)
        self.rag_store.populate_truth_timeline(case.truth_timeline)

        # Check if there is a saved in-progress active session for this daily case
        saved_active = self.progress_data.get("active_session")
        if not is_practice and saved_active and saved_active.get("date") == case.date:
            saved_diff = saved_active.get("difficulty", difficulty)
            self.difficulty = saved_diff
            self.session = GameSession(
                case=case,
                difficulty=saved_diff,
                remaining_tokens=saved_active.get("remaining_tokens", max_tok),
                max_tokens=saved_active.get("max_tokens", max_tok),
                hint_used=saved_active.get("hint_used", False),
                session_id=session_id,
                transcript=[Statement(**s) for s in saved_active.get("transcript", [])],
                ledger=[AtomicClaim(**c) for c in saved_active.get("ledger", [])]
            )
            # Re-index existing statements into RAG store
            for stmt in self.session.transcript:
                self.rag_store.add_suspect_statement(
                    turn=stmt.turn_number,
                    answer=stmt.answer,
                    claims=stmt.extracted_claims
                )
        else:
            self.session = GameSession(
                case=case,
                difficulty=difficulty,
                remaining_tokens=max_tok,
                max_tokens=max_tok,
                session_id=session_id
            )

        # Initialize Agents with RAG
        self.suspect_agent = SuspectAgent(self.client, self.rag_store)
        self.claim_extractor = ClaimExtractorAgent(self.client, self.rag_store)
        self.judge_agent = ContradictionJudgeAgent(self.client, self.rag_store)

    def _save_active_session(self):
        """Save mid-game state to disk so closing the game preserves all progress and turns."""
        if not self.session or getattr(self, "is_practice", False) or self.session.game_over:
            return
        self.progress_data["active_session"] = {
            "date": self.session.case.date,
            "difficulty": getattr(self, "difficulty", "classic"),
            "remaining_tokens": self.session.remaining_tokens,
            "max_tokens": self.session.max_tokens,
            "hint_used": self.session.hint_used,
            "transcript": [s.model_dump() for s in self.session.transcript],
            "ledger": [c.model_dump() for c in self.session.ledger]
        }
        self._save_progress()

    def ask_question(self, question: str) -> Tuple[bool, str, Optional[Statement]]:
        """Process player question: deducts 1 token, calls Suspect Agent, extracts claims, updates transcript."""
        if not self.session:
            return False, "Session not initialized", None
        if self.session.game_over:
            return False, "Game is already over.", None
        if self.session.remaining_tokens <= 0:
            return False, "Out of question tokens!", None

        # Validate input
        clean_q = question.strip()
        if not clean_q:
            return False, "Question cannot be empty.", None
        if len(clean_q) > 200:
            return False, "Question exceeds 200 characters limit.", None

        # Deduct token
        self.session.remaining_tokens -= 1
        self.audio.play_sfx("token_spent")

        # Suspect Agent response
        suspect_resp = self.suspect_agent.interrogate(
            question=clean_q,
            case=self.session.case,
            remaining_tokens=self.session.remaining_tokens,
            transcript=self.session.transcript
        )

        turn = len(self.session.transcript) + 1

        # Claim Extractor
        atomic_claims = self.claim_extractor.extract_and_store(
            turn_number=turn,
            spoken_answer=suspect_resp.spoken_answer
        )
        self.session.ledger.extend(atomic_claims)

        # Audio cue if nervous/panicked
        if suspect_resp.emotion in ["nervous", "panicked"]:
            self.audio.play_sfx("suspect_nervous")

        stmt = Statement(
            turn_number=turn,
            question=clean_q,
            answer=suspect_resp.spoken_answer,
            emotion=suspect_resp.emotion,
            inner_reasoning=suspect_resp.inner_reasoning,
            extracted_claims=atomic_claims
        )
        self.session.transcript.append(stmt)
        self._save_active_session()

        # Check if out of tokens without accusation
        if self.session.remaining_tokens <= 0 and not self.session.game_over:
            self.session.game_over = True
            self.session.won = False
            self.audio.play_music("lose", loop=False)
            self._record_game_end(won=False)

        return True, "", stmt

    def use_hint(self) -> Tuple[bool, str]:
        """Provides one noir hint at the cost of 1 token (behavior depends on difficulty)."""
        if not self.session:
            return False, "No active game."
        diff = getattr(self, "difficulty", "classic")
        if diff == "hardboiled":
            return False, "Hints are strictly forbidden in Hardboiled Noir difficulty. Rely on your own detective instincts!"
        if diff != "rookie" and self.session.hint_used:
            return False, "You have already used your 1 hint for this case."
        if self.session.remaining_tokens <= 1:
            return False, "Not enough tokens to afford a hint (costs 1 token, need at least 1 remaining to question/accuse)."

        self.session.remaining_tokens -= 1
        self.session.hint_used = True
        self._save_active_session()
        self.audio.play_sfx("token_spent")
        hint_text = self.narrator_agent.generate_hint(self.session.case)
        return True, hint_text

    def accuse(self, quote: str, target_text: str, is_dossier_fact: bool = True) -> AccusationResult:
        """Process accusation through Contradiction Judge."""
        if not self.session or not self.judge_agent:
            raise RuntimeError("Session or Judge not initialized.")

        self.audio.play_sfx("accuse_stamp")
        result = self.judge_agent.judge_accusation(
            quote=quote,
            target_text=target_text,
            case=self.session.case,
            is_dossier_fact=is_dossier_fact
        )
        self.session.accusation_result = result

        if result.valid:
            # Won the game!
            self.session.won = True
            self.session.game_over = True
            self.audio.play_music("win", loop=False)
            self._record_game_end(won=True)
        else:
            # Invalid accusation: penalty based on difficulty
            penalty = 2 if getattr(self, "difficulty", "classic") == "hardboiled" else 1
            self.session.remaining_tokens = max(0, self.session.remaining_tokens - penalty)
            if self.session.remaining_tokens <= 0:
                self.session.won = False
                self.session.game_over = True
                self.audio.play_music("lose", loop=False)
                self._record_game_end(won=False)
            else:
                self._save_active_session()

        return result

    def _record_game_end(self, won: bool):
        """Update save progress, calculate detective score, and maintain streaks (skips practice sessions)."""
        if not self.session or getattr(self, "is_practice", False):
            return
        date_str = self.session.case.date
        tokens_left = self.session.remaining_tokens
        turns_taken = len(self.session.transcript)
        diff = getattr(self, "difficulty", "classic")
        hint_used = getattr(self.session, "hint_used", False)

        cur_streak = self.progress_data.get("current_streak", 0)
        new_streak = (cur_streak + 1) if won else 0

        score_info = calculate_score(
            won=won,
            remaining_tokens=tokens_left,
            turns_taken=turns_taken,
            hint_used=hint_used,
            difficulty=diff,
            streak=new_streak
        )
        self.last_score_info = score_info

        prev_entry = self.progress_data.get("completed_dates", {}).get(date_str)
        already_completed = prev_entry is not None

        if not already_completed:
            self.progress_data["games_played"] = self.progress_data.get("games_played", 0) + 1
            if won:
                self.progress_data["games_won"] = self.progress_data.get("games_won", 0) + 1
                self.progress_data["current_streak"] = new_streak
                if new_streak > self.progress_data.get("max_streak", 0):
                    self.progress_data["max_streak"] = new_streak
                earned = score_info["total"]
                self.progress_data["total_score"] = self.progress_data.get("total_score", 0) + earned
                if earned > self.progress_data.get("high_score", 0):
                    self.progress_data["high_score"] = earned
            else:
                self.progress_data["current_streak"] = 0

            self.progress_data["last_played_date"] = date_str

        self.progress_data.setdefault("completed_dates", {})[date_str] = {
            "won": won,
            "score": score_info["total"],
            "score_breakdown": score_info,
            "tokens_left": tokens_left,
            "turns_taken": turns_taken,
            "difficulty": diff,
            "hint_used": hint_used,
            "share_grid": self.generate_share_grid(),
            "completed_at": datetime.now().isoformat()
        }
        self.progress_data["active_session"] = None
        self._save_progress()
        return score_info

    def generate_share_grid(self) -> str:
        """Generate Wordle-style share grid."""
        if not self.session:
            return ""
        case_id = self.session.case.id
        won = self.session.won
        tokens_left = self.session.remaining_tokens
        tokens_used = 5 - tokens_left

        # Generate emoji blocks: 🔍 for questions asked, 💥 for winning catch, ⬛ for remaining/failed
        emojis = []
        for i in range(5):
            if i < tokens_used - (1 if won else 0):
                emojis.append("🔍")
            elif won and i == tokens_used - 1:
                emojis.append("💥")
            else:
                emojis.append("⬛")

        grid_line = "".join(emojis)
        status_line = f"Caught in {tokens_used}/5" if won else "Suspect walked free (0/5)"
        return f"THE ALIBI [{self.session.case.date}]\n{grid_line}\n{status_line}"

    @staticmethod
    def get_time_until_midnight() -> str:
        """Countdown string HH:MM:SS until next midnight."""
        now = datetime.now()
        tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        remaining = tomorrow - now
        total_seconds = int(remaining.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
