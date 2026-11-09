from typing import List, Optional, Literal, Any
from pydantic import BaseModel, Field, model_validator

class VerifiedFact(BaseModel):
    id: str = Field(description="Unique identifier for the fact, e.g. fact-1")
    text: str = Field(description="The verified forensic fact description")

class TimelineEvent(BaseModel):
    time: str = Field(description="Time of the occurrence, e.g. 11:15 PM")
    event: str = Field(description="What really happened at this time")

class LieWeakPoint(BaseModel):
    id: str = Field(description="Identifier for the weak point, e.g. wp-1")
    claim: str = Field(description="The false claim the suspect plans to make")
    conflicts_with: str = Field(description="Which verified fact id or event it conflicts with, e.g. fact-1")
    trigger_topics: List[str] = Field(default_factory=list, description="Question topics likely to trigger this weak point")
    planned_slip: str = Field(description="The planned slip sentence containing the contradiction")

class LiePlan(BaseModel):
    cover_story: str = Field(description="The general cover story the suspect will tell")
    weak_points: List[LieWeakPoint] = Field(default_factory=list, description="3 to 5 planned weak points")

class SuspectProfile(BaseModel):
    name: str = Field(description="Suspect's full name")
    occupation: str = Field(description="Suspect's trade or eccentric occupation")
    quirk: str = Field(description="Distinctive speech quirk or rhetorical obsession")

class Case(BaseModel):
    id: str = Field(description="Unique case identifier")
    date: str = Field(description="Case date in YYYY-MM-DD format")
    title: str = Field(description="Bizarre or humorous case title")
    crime_description: str = Field(description="Description of the micro-crime")
    setting: str = Field(description="Atmospheric location of the incident")
    suspect: SuspectProfile = Field(description="Profile of the eccentric suspect")
    dossier: List[VerifiedFact] = Field(description="Exactly 3 verified forensic facts")
    truth_timeline: List[TimelineEvent] = Field(description="True timeline of what actually happened (hidden from player)")
    lie_plan: LiePlan = Field(description="Planned cover story and exploitable weak points")
    solution_contradictions: List[str] = Field(default_factory=list, description="Guaranteed catchable contradictions for victory")

class AtomicClaim(BaseModel):
    subject: str = Field(default="", description="Subject of the claim")
    predicate: str = Field(default="", description="Action or state asserted")
    time: Optional[str] = Field(default=None, description="Time mentioned if any")
    place: Optional[str] = Field(default=None, description="Location mentioned if any")
    object: Optional[str] = Field(default=None, description="Object or entity involved")

class Statement(BaseModel):
    turn_number: int
    question: str
    answer: str
    emotion: Literal["calm", "nervous", "defensive", "smug", "panicked"] = "calm"
    inner_reasoning: Optional[str] = None
    extracted_claims: List[AtomicClaim] = Field(default_factory=list)

class AccusationResult(BaseModel):
    valid: bool
    verdict: Literal["VALID", "INVALID"]
    explanation: str
    highlighted_quote: str
    target_text: str
    contradiction_category: Optional[str] = None
    breakdown_confession: Optional[str] = None

class GameSession(BaseModel):
    case: Case
    difficulty: Literal["classic", "hardboiled", "rookie"] = "classic"
    remaining_tokens: int = 5
    max_tokens: int = 5
    transcript: List[Statement] = Field(default_factory=list)
    ledger: List[AtomicClaim] = Field(default_factory=list)
    accusation_result: Optional[AccusationResult] = None
    hint_used: bool = False
    game_over: bool = False
    won: bool = False
    session_id: str = ""

# Agent Output Schemas for Structured JSON validation

class SuspectToolCall(BaseModel):
    tool: Literal["lookup_my_prior_statements", "lookup_dossier", "lookup_truth", "plan_lie"]
    topic: str = Field(default="", description="Topic or query for the tool lookup")

class SuspectResponse(BaseModel):
    tool_call: Optional[SuspectToolCall] = None
    inner_reasoning: str = Field(description="Hidden reasoning for strategy and lie consistency")
    spoken_answer: str = Field(description="The in-character spoken answer to the detective (under 60 words)")
    emotion: Literal["calm", "nervous", "defensive", "smug", "panicked"] = Field(
        default="calm", description="Emotional demeanor"
    )

class ExtractedClaimsResponse(BaseModel):
    claims: List[AtomicClaim] = Field(default_factory=list)

class CaseValidationResult(BaseModel):
    is_valid: bool
    contradiction_count: int
    facts_consistent: bool
    reason: str

class JudgeEvaluation(BaseModel):
    claim_a_neutral: str = Field(default="", description="Neutral restatement of the highlighted suspect quote")
    claim_b_neutral: str = Field(default="", description="Neutral restatement of the target dossier fact or earlier statement")
    logical_incompatibility: str = Field(default="", description="Step-by-step reasoning on whether claim A and claim B cannot both be true simultaneously")
    verdict: Literal["VALID", "INVALID"] = Field(default="INVALID", description="VALID if logically incompatible, INVALID otherwise")
    narration: str = Field(default="", description="One dry noir narrator sentence explaining the ruling")

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        normalized = {}
        for k, v in data.items():
            clean_k = str(k).lower().replace(" ", "_").replace("-", "_")
            normalized[clean_k] = v

        res = {}
        # verdict extraction with strict case-insensitivity
        v_val = normalized.get("verdict") or normalized.get("verdict_value") or "INVALID"
        res["verdict"] = "VALID" if str(v_val).strip().upper() == "VALID" else "INVALID"

        # narration / explanation
        res["narration"] = str(
            normalized.get("narration") or normalized.get("explanation") or normalized.get("reasoning") or normalized.get("reason") or ""
        )

        # claim a
        res["claim_a_neutral"] = str(
            normalized.get("claim_a_neutral") or normalized.get("claim_a") or normalized.get("claima") or normalized.get("suspect_claim") or ""
        )

        # claim b
        res["claim_b_neutral"] = str(
            normalized.get("claim_b_neutral") or normalized.get("claim_b") or normalized.get("claimb") or normalized.get("target_fact") or ""
        )

        # logical incompatibility
        res["logical_incompatibility"] = str(
            normalized.get("logical_incompatibility") or normalized.get("mutual_exclusivity") or normalized.get("incompatibility") or normalized.get("incompatible") or ""
        )
        return res
