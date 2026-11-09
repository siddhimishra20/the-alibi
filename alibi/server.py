import os
import time
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from alibi.llm.client import OllamaClient
from alibi.agents.case_architect import CaseArchitectAgent
from alibi.game.session import GameManager
from alibi.ui.ascii_art import ASCII_FACES, get_suspect_face

app = FastAPI(title="THE ALIBI - Web API", description="Satirical Noir Detective Micro-Crime Game API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global game engine singletons
client = OllamaClient()
architect = CaseArchitectAgent(client=client)
game_manager = GameManager(client=client)

# In-memory sessions store
active_sessions: Dict[str, GameManager] = {}

class StartSessionRequest(BaseModel):
    date: Optional[str] = None
    practice: bool = False
    difficulty: str = "classic"  # classic, hardboiled, rookie

class InterrogateRequest(BaseModel):
    session_id: str
    question: str

class AccuseRequest(BaseModel):
    session_id: str
    quote: str
    target_text: str
    is_dossier_fact: bool = True

class HintRequest(BaseModel):
    session_id: str

class LLMConfigRequest(BaseModel):
    provider: str = "groq"  # "ollama" or "groq"
    groq_api_key: Optional[str] = None
    groq_model: Optional[str] = "llama-3.1-8b-instant"

def sanitize_case_for_client(case_obj) -> Dict[str, Any]:
    """Sanitize case object so spoilers (truth timeline, weak points) are hidden from players."""
    s_name = case_obj.suspect.name
    face_art = get_suspect_face(s_name)

    return {
        "id": case_obj.id,
        "date": case_obj.date,
        "title": case_obj.title,
        "crime_description": case_obj.crime_description,
        "setting": case_obj.setting,
        "suspect": {
            "name": case_obj.suspect.name,
            "occupation": case_obj.suspect.occupation,
            "quirk": case_obj.suspect.quirk,
            "ascii_face": face_art
        },
        "dossier": [
            {"id": f.id, "text": f.text} for f in case_obj.dossier
        ]
    }

@app.get("/api/status")
def get_status():
    installed = client.get_installed_models()
    verified, msg = client.verify_models()
    today_str = time.strftime("%Y-%m-%d")
    is_today_solved = game_manager.get_completed_result(today_str) is not None

    return {
        "status": "online",
        "provider": client.provider,
        "models_verified": verified,
        "installed_models": installed,
        "today": today_str,
        "today_solved": is_today_solved,
        "games_played": game_manager.progress_data.get("games_played", 0),
        "games_won": game_manager.progress_data.get("games_won", 0),
        "current_streak": game_manager.progress_data.get("current_streak", 0),
        "max_streak": game_manager.progress_data.get("max_streak", 0)
    }

@app.get("/api/config/llm")
def get_llm_config():
    verified, msg = client.verify_models()
    return {
        "provider": client.provider,
        "has_groq_key": bool(client.groq_api_key),
        "groq_model": getattr(client, "groq_model", "llama-3.1-8b-instant"),
        "ollama_model": getattr(client, "model", "llama3.1:latest"),
        "models_verified": verified,
        "status_message": msg
    }

@app.post("/api/config/llm")
def set_llm_config(req: LLMConfigRequest):
    if req.groq_api_key:
        client.groq_api_key = req.groq_api_key.strip()
        os.environ["GROQ_API_KEY"] = client.groq_api_key
    if req.groq_model:
        client.groq_model = req.groq_model.strip()
    client.provider = req.provider.lower()
    os.environ["LLM_PROVIDER"] = client.provider

    verified, msg = client.verify_models()
    return {
        "success": True,
        "provider": client.provider,
        "verified": verified,
        "message": msg
    }

@app.get("/api/case/today")
def get_today_case():
    case = architect.get_daily_case(practice=False)
    return sanitize_case_for_client(case)

@app.get("/api/case/{date_str}")
def get_case_by_date(date_str: str):
    case = architect.get_daily_case(date_str=date_str, practice=False)
    return sanitize_case_for_client(case)

@app.get("/api/archive")
def get_archive():
    return architect.registry.get_archive_list(game_manager.progress_data)

@app.post("/api/session/start")
def start_session(req: StartSessionRequest):
    case = architect.get_daily_case(date_str=req.date, practice=req.practice)
    session_id = f"sess_{int(time.time() * 1000)}"

    gm = GameManager(client=client)
    gm.init_session(case, is_practice=req.practice, difficulty=req.difficulty)
    active_sessions[session_id] = gm

    return {
        "session_id": session_id,
        "case": sanitize_case_for_client(case),
        "difficulty": req.difficulty,
        "remaining_tokens": gm.session.remaining_tokens,
        "max_tokens": gm.session.max_tokens,
        "is_practice": req.practice
    }

@app.post("/api/session/interrogate")
def interrogate(req: InterrogateRequest):
    gm = active_sessions.get(req.session_id)
    if not gm or not gm.session:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    success, err_msg, statement = gm.ask_question(req.question)
    if not success:
        return {
            "success": False,
            "error": err_msg,
            "remaining_tokens": gm.session.remaining_tokens,
            "game_over": gm.session.game_over
        }

    return {
        "success": True,
        "turn_number": statement.turn_number,
        "question": statement.question,
        "answer": statement.answer,
        "emotion": statement.emotion,
        "remaining_tokens": gm.session.remaining_tokens,
        "max_tokens": gm.session.max_tokens,
        "game_over": gm.session.game_over,
        "won": gm.session.won,
        "extracted_claims": [c.model_dump() for c in statement.extracted_claims]
    }

@app.post("/api/session/accuse")
def accuse(req: AccuseRequest):
    gm = active_sessions.get(req.session_id)
    if not gm or not gm.session:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    result = gm.accuse(req.quote, req.target_text, req.is_dossier_fact)

    return {
        "valid": result.valid,
        "verdict": result.verdict,
        "explanation": result.explanation,
        "breakdown_confession": result.breakdown_confession,
        "remaining_tokens": gm.session.remaining_tokens,
        "game_over": gm.session.game_over,
        "won": gm.session.won,
        "share_grid": gm.generate_share_grid() if gm.session.game_over else ""
    }

@app.post("/api/session/hint")
def get_hint(req: HintRequest):
    gm = active_sessions.get(req.session_id)
    if not gm or not gm.session:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    success, hint_or_err = gm.use_hint()
    return {
        "success": success,
        "hint": hint_or_err,
        "remaining_tokens": gm.session.remaining_tokens
    }

# Mount static files for the web frontend
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/")
    def index():
        return FileResponse(os.path.join(static_dir, "index.html"))
