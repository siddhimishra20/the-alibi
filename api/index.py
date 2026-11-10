import os
import sys

# Ensure project root is available on sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Configure environment for Vercel serverless execution
os.environ["VERCEL"] = "1"
if not os.getenv("LLM_PROVIDER") and os.getenv("GROQ_API_KEY"):
    os.environ["LLM_PROVIDER"] = "groq"

from alibi.server import app

# Export FastAPI app as ASGI handler for Vercel
handler = app
app = app
