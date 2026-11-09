import os
import time
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse, Response
from pydantic import BaseModel

from alibi.llm.client import OllamaClient
from alibi.agents.case_architect import CaseArchitectAgent
from alibi.game.session import GameManager
from alibi.game.scoring import calculate_score, get_detective_rank
from alibi.character import get_suspect_png_bytes, pick_traits, describe_traits
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
    seed_key = getattr(case_obj, "id", None) or getattr(case_obj, "date", None) or s_name
    try:
        traits, _ = pick_traits(seed_key)
        trait_desc = describe_traits(traits)
    except Exception:
        trait_desc = ""

    portrait_url = f"/api/character/{seed_key}.png"

    return {
        "id": case_obj.id,
        "date": case_obj.date,
        "title": case_obj.title,
        "crime_description": case_obj.crime_description,
        "setting": case_obj.setting,
        "portrait_url": portrait_url,
        "suspect": {
            "name": case_obj.suspect.name,
            "occupation": case_obj.suspect.occupation,
            "quirk": case_obj.suspect.quirk,
            "ascii_face": face_art,
            "portrait_url": portrait_url,
            "traits_description": trait_desc
        },
        "dossier": [
            {"id": f.id, "text": f.text} for f in case_obj.dossier
        ]
    }

@app.api_route("/api/character/{seed}.png", methods=["GET", "HEAD"])
def get_character_portrait(seed: str, scale: int = 6, crt: bool = True):
    """Serve procedurally-generated pixel-art suspect portrait as PNG."""
    try:
        png_bytes = get_suspect_png_bytes(seed, scale=scale, crt=crt)
        return Response(content=png_bytes, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate character: {e}")

@app.get("/api/status")
def get_status():
    installed = client.get_installed_models()
    verified, msg = client.verify_models()
    today_str = time.strftime("%Y-%m-%d")
    today_entry = game_manager.get_completed_result(today_str)
    is_today_solved = today_entry is not None and today_entry.get("won", False)

    total_score = game_manager.progress_data.get("total_score", 0)
    high_score = game_manager.progress_data.get("high_score", 0)
    rank_info = get_detective_rank(total_score)

    return {
        "status": "online",
        "provider": client.provider,
        "models_verified": verified,
        "installed_models": installed,
        "today": today_str,
        "today_solved": is_today_solved,
        "today_data": today_entry,
        "countdown_midnight": GameManager.get_time_until_midnight(),
        "total_score": total_score,
        "high_score": high_score,
        "rank": rank_info["rank"],
        "rank_tier": rank_info["tier"],
        "rank_next": rank_info["next_tier"],
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

    already_solved = (not req.practice) and (gm.get_completed_result(case.date) is not None)
    completed_data = gm.get_completed_result(case.date) if already_solved else None

    return {
        "session_id": session_id,
        "case": sanitize_case_for_client(case),
        "difficulty": req.difficulty,
        "remaining_tokens": gm.session.remaining_tokens,
        "max_tokens": gm.session.max_tokens,
        "is_practice": req.practice,
        "already_solved": already_solved,
        "completed_data": completed_data
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

    tot_score = gm.progress_data.get("total_score", 0)
    rank_info = get_detective_rank(tot_score)

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
        "score_info": getattr(gm, "last_score_info", None),
        "total_score": tot_score,
        "rank": rank_info["rank"],
        "extracted_claims": [c.model_dump() for c in statement.extracted_claims]
    }

@app.post("/api/session/accuse")
def accuse(req: AccuseRequest):
    gm = active_sessions.get(req.session_id)
    if not gm or not gm.session:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    result = gm.accuse(req.quote, req.target_text, req.is_dossier_fact)
    tot_score = gm.progress_data.get("total_score", 0)
    rank_info = get_detective_rank(tot_score)

    return {
        "valid": result.valid,
        "verdict": result.verdict,
        "explanation": result.explanation,
        "breakdown_confession": result.breakdown_confession,
        "remaining_tokens": gm.session.remaining_tokens,
        "game_over": gm.session.game_over,
        "won": gm.session.won,
        "score_info": getattr(gm, "last_score_info", None),
        "total_score": tot_score,
        "rank": rank_info["rank"],
        "rank_tier": rank_info["tier"],
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

# Mount static files for the web frontend and audio assets
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "static")
audio_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "audio")

if os.path.exists(audio_dir):
    app.mount("/audio", StaticFiles(directory=audio_dir), name="audio")

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", response_class=HTMLResponse)
    def index():
        html_file = os.path.join(static_dir, "index.html")
        with open(html_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())

    @app.get("/favicon.ico")
    def favicon():
        return JSONResponse(status_code=204, content=None)
