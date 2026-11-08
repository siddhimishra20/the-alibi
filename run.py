import os
import sys

# Auto-re-execute using project virtual environment if invoked outside it
_venv_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".venv")
_venv_python = os.path.join(_venv_dir, "bin", "python")
if os.path.exists(_venv_python) and sys.prefix != _venv_dir:
    os.execv(_venv_python, [_venv_python] + sys.argv)

import argparse
import subprocess
from dotenv import load_dotenv

from alibi.llm.client import OllamaClient
from alibi.audio.synthesizer import ensure_all_audio_assets

def startup_model_check() -> OllamaClient:
    """Check Ollama connectivity and verify models interactively at startup."""
    load_dotenv()
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "")
    embed_model = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text:latest")

    client = OllamaClient(base_url=host, model=model or "llama3.1:latest", embed_model=embed_model)
    installed = client.get_installed_models()

    if not installed:
        print("\n" + "=" * 60)
        print("[!] ERROR: Could not connect to Ollama at", host)
        print("Please ensure Ollama is installed and running locally:")
        print("    ollama serve")
        print("=" * 60 + "\n")
        sys.exit(1)

    print("\n--- [ THE ALIBI: LOCAL LLM INITIALIZATION ] ---")
    print(f"Ollama detected at: {host}")
    print(f"Available local models: {', '.join(installed)}")

    # Check embedding model
    has_embed = any(m == embed_model or m.startswith("nomic-embed-text") for m in installed)
    if not has_embed:
        print(f"\n[!] Required embedding model '{embed_model}' is not installed.")
        print("To install it, run:")
        print("    ollama pull nomic-embed-text")
        choice = input("Would you like to run this command now? (y/N): ").strip().lower()
        if choice in ['y', 'yes']:
            print("Pulling nomic-embed-text...")
            subprocess.run(["ollama", "pull", "nomic-embed-text"], check=True)
            embed_model = "nomic-embed-text:latest"
        else:
            print("Cannot continue without local embedding model. Exiting.")
            sys.exit(1)

    # Check chat model
    has_chat = any(m == model or m.startswith(model.split(":")[0]) for m in installed) if model else False
    if not model or not has_chat:
        # Prompt user to choose from installed models
        print(f"\nTarget model '{model}' is unset or not found.")
        print("Please select one of your installed models:")
        chat_candidates = [m for m in installed if not "embed" in m.lower()]
        if not chat_candidates:
            chat_candidates = installed

        for idx, m_name in enumerate(chat_candidates, 1):
            print(f"  [{idx}] {m_name}")
        
        while True:
            choice = input(f"Select model number (1-{len(chat_candidates)}) [default 1]: ").strip()
            if not choice:
                chosen_model = chat_candidates[0]
                break
            try:
                val = int(choice)
                if 1 <= val <= len(chat_candidates):
                    chosen_model = chat_candidates[val - 1]
                    break
            except ValueError:
                pass
            print("Invalid selection. Try again.")

        model = chosen_model
        print(f"Using chat model: {model}\n")

    client.model = model
    client.embed_model = embed_model
    return client

def main():
    parser = argparse.ArgumentParser(description="THE ALIBI: A Daily Micro-Crime Interrogation Game")
    parser.add_argument("--practice", action="store_true", help="Launch directly in practice mode with an uncompleted randomized case")
    parser.add_argument("--cli", action="store_true", help="Launch in simple line-based CLI mode instead of full-screen Textual TUI")
    parser.add_argument("--web", action="store_true", help="Launch the Web Application (FastAPI + Retro Noir UI) on http://127.0.0.1:8000")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the web server (default: 8000)")
    parser.add_argument("--pre-generate", type=int, metavar="DAYS", help="Pre-generate the next N days of unique daily cases ahead of time")
    parser.add_argument("--install-cron", action="store_true", help="Install weekly Monday 00:00 cron job for automated pre-generation")
    parser.add_argument("--uninstall-cron", action="store_true", help="Uninstall the weekly cron job")
    parser.add_argument("--install-launchd", action="store_true", help="Install macOS launchd background agent")
    parser.add_argument("--daemon", action="store_true", help="Run background daemon maintaining a rolling case buffer")
    args = parser.parse_args()

    # Pre-generate audio assets
    ensure_all_audio_assets("assets/audio")

    # Scheduler and Cron commands
    if args.install_cron:
        from scripts.scheduler import install_cron
        install_cron(days=14)
        return

    if args.uninstall_cron:
        from scripts.scheduler import uninstall_cron
        uninstall_cron()
        return

    if args.install_launchd:
        from scripts.scheduler import install_launchd
        install_launchd(days=14)
        return

    if args.daemon:
        from scripts.scheduler import run_daemon_loop
        run_daemon_loop(target_buffer_days=14)
        return

    # Verify models
    client = startup_model_check()

    if args.web:
        import uvicorn
        from alibi.server import app as fastapi_app
        print(f"\n[+] Starting THE ALIBI Web Application on http://127.0.0.1:{args.port} ...\n")
        uvicorn.run(fastapi_app, host="127.0.0.1", port=args.port)
        return

    if args.pre_generate:
        from alibi.agents.case_architect import CaseArchitectAgent
        architect = CaseArchitectAgent(client)
        architect.pre_generate_schedule(days=args.pre_generate)
        return

    if args.cli:
        from alibi.game.session import GameManager
        from alibi.agents.case_architect import CaseArchitectAgent
        from alibi.ui.cli import run_cli_game
        from datetime import datetime

        gm = GameManager(client)
        architect = CaseArchitectAgent(client)
        today = datetime.now().strftime("%Y-%m-%d")
        case = architect.get_daily_case(date_str=today, practice=args.practice)
        run_cli_game(gm, case, is_practice=args.practice)
        return

    # Launch Textual App
    from alibi.ui.app import TheAlibiApp
    app = TheAlibiApp(client=client)

    if args.practice:
        # Override initial screen to start game in practice mode immediately
        def on_app_ready():
            app.start_game(is_practice=True)
        app.call_after_refresh(on_app_ready)

    app.run()

if __name__ == "__main__":
    main()
