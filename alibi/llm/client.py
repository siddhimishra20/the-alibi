import os
import json
import time
import re
from typing import List, Dict, Any, Optional, Generator, Tuple
import httpx
from dotenv import load_dotenv

load_dotenv()

class OllamaClient:
    """Client for local Ollama server with streaming, json validation, embeddings, and repair."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        embed_model: Optional[str] = None,
        log_file: Optional[str] = None
    ):
        self.base_url = (base_url or os.getenv("OLLAMA_HOST") or "http://localhost:11434").rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.1:latest")
        self.embed_model = embed_model or os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text:latest")
        if log_file is None:
            log_file = "/tmp/logs/session.jsonl" if os.getenv("VERCEL") else "logs/session.jsonl"
        self.log_file = log_file
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        self.last_trace: List[Dict[str, Any]] = []

        # Cloud API Support (Groq, OpenAI-compatible)
        self.groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
        self.provider = os.getenv("LLM_PROVIDER", "").lower()
        if not self.provider:
            self.provider = "groq" if self.groq_api_key else "ollama"
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        self.groq_base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/")

    def get_installed_models(self) -> List[str]:
        """Fetch list of installed models from Ollama /api/tags or cloud provider."""
        if self.provider == "groq" and self.groq_api_key:
            return [self.groq_model]

        try:
            resp = httpx.get(f"{self.base_url}/api/tags", timeout=5.0)
            if resp.status_code == 200:
                data = resp.json()
                return [m.get("name", "") for m in data.get("models", [])]
        except Exception as e:
            pass
        return []

    def verify_models(self) -> Tuple[bool, str]:
        """Verify chat model and embedding model are installed and available."""
        if self.provider == "groq":
            if not self.groq_api_key:
                return False, "LLM_PROVIDER is set to 'groq', but GROQ_API_KEY environment variable is missing."
            return True, f"Groq Cloud active (model: {self.groq_model})"

        installed = self.get_installed_models()
        if not installed:
            return False, f"Could not connect to Ollama at {self.base_url}. Is Ollama running?"

        # Match model (handling tags like :latest or :8b)
        def model_match(target: str, list_models: List[str]) -> bool:
            base_target = target.split(":")[0]
            for m in list_models:
                if m == target or m.split(":")[0] == base_target:
                    return True
            return False

        if not model_match(self.model, installed):
            return False, f"OLLAMA_MODEL '{self.model}' is not installed. Installed models: {', '.join(installed)}"

        if not model_match(self.embed_model, installed):
            cmd = f"ollama pull {self.embed_model.split(':')[0]}"
            return False, f"Embedding model '{self.embed_model}' is not installed.\nPlease run: `{cmd}`"

        return True, "Models verified."

    def log_call(self, agent_name: str, prompt: str, response: str, latency: float, model: str, extra: Optional[Dict] = None):
        """Append LLM call record to logs/session.jsonl and memory trace."""
        record = {
            "timestamp": time.time(),
            "iso_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "agent": agent_name,
            "model": model,
            "prompt": prompt,
            "response": response,
            "latency_ms": round(latency * 1000, 1),
            "extra": extra or {}
        }
        self.last_trace.append(record)
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception:
            pass

    def get_embeddings(self, text: str) -> List[float]:
        """Generate embedding vector using nomic-embed-text."""
        payload = {
            "model": self.embed_model,
            "prompt": text
        }
        try:
            resp = httpx.post(f"{self.base_url}/api/embeddings", json=payload, timeout=20.0)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("embedding", [])
        except Exception as e:
            pass
        return []

    def clean_json_text(self, text: str) -> str:
        """Strip markdown fences, trailing commas, or surrounding commentary."""
        text = text.strip()
        # Strip ```json ... ```
        if "```" in text:
            # find first { or [
            match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
            if match:
                text = match.group(1).strip()
            else:
                text = re.sub(r'^```[a-zA-Z]*\n', '', text)
                text = re.sub(r'\n```$', '', text).strip()

        # Extract only the outermost JSON object or array if extra preamble exists
        first_brace = text.find("{")
        first_bracket = text.find("[")
        if first_brace != -1 and (first_bracket == -1 or first_brace < first_bracket):
            last_brace = text.rfind("}")
            if last_brace != -1:
                text = text[first_brace:last_brace + 1]
        elif first_bracket != -1:
            last_bracket = text.rfind("]")
            if last_bracket != -1:
                text = text[first_bracket:last_bracket + 1]

        # Fix trailing commas before } or ]
        text = re.sub(r',\s*([\]}])', r'\1', text)
        return text

    def _generate_groq(
        self,
        prompt: str,
        system: Optional[str],
        temperature: float,
        format_json: bool,
        agent_name: str,
        num_predict: Optional[int],
        start: float
    ) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload: Dict[str, Any] = {
            "model": self.groq_model,
            "messages": messages,
            "temperature": temperature,
        }
        if num_predict is not None:
            payload["max_tokens"] = num_predict
        if format_json:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json"
        }

        try:
            resp = httpx.post(f"{self.groq_base_url}/chat/completions", json=payload, headers=headers, timeout=60.0)
            resp.raise_for_status()
            data = resp.json()
            raw_text = data["choices"][0]["message"]["content"]
            duration = time.time() - start
            self.log_call(agent_name, prompt, raw_text, duration, self.groq_model, {"provider": "groq", "system": system})
            return raw_text
        except Exception as e:
            duration = time.time() - start
            err_msg = f"Error calling Groq API: {e}"
            self.log_call(agent_name, prompt, err_msg, duration, self.groq_model, {"error": str(e)})
            raise

    def _generate_stream_groq(
        self,
        prompt: str,
        system: Optional[str],
        temperature: float,
        format_json: bool,
        agent_name: str,
        start: float
    ) -> Generator[str, None, str]:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload: Dict[str, Any] = {
            "model": self.groq_model,
            "messages": messages,
            "temperature": temperature,
            "stream": True
        }
        if format_json:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json"
        }

        accumulated = []
        with httpx.stream("POST", f"{self.groq_base_url}/chat/completions", json=payload, headers=headers, timeout=60.0) as r:
            for line in r.iter_lines():
                if not line:
                    continue
                if line.startswith("data: "):
                    data_str = line[6:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        token = delta.get("content", "")
                        if token:
                            accumulated.append(token)
                            yield token
                    except Exception:
                        continue

        full_response = "".join(accumulated)
        duration = time.time() - start
        self.log_call(agent_name, prompt, full_response, duration, self.groq_model, {"provider": "groq", "stream": True})
        return full_response

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        format_json: bool = False,
        agent_name: str = "LLM",
        num_predict: Optional[int] = None
    ) -> str:
        """Generate a complete completion synchronously."""
        start = time.time()
        if self.provider == "groq" and self.groq_api_key:
            return self._generate_groq(prompt, system, temperature, format_json, agent_name, num_predict, start)
        options = {
            "temperature": temperature,
            "num_ctx": 2048
        }
        if num_predict is not None:
            options["num_predict"] = num_predict

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": options
        }
        if system:
            payload["system"] = system
        if format_json:
            payload["format"] = "json"

        try:
            resp = httpx.post(f"{self.base_url}/api/generate", json=payload, timeout=90.0)
            resp.raise_for_status()
            data = resp.json()
            raw_text = data.get("response", "")
            duration = time.time() - start
            self.log_call(agent_name, prompt, raw_text, duration, self.model, {"system": system, "temperature": temperature})
            return raw_text
        except Exception as e:
            duration = time.time() - start
            err_msg = f"Error calling Ollama generate: {e}"
            self.log_call(agent_name, prompt, err_msg, duration, self.model, {"error": str(e)})
            raise

    def generate_stream(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        format_json: bool = False,
        agent_name: str = "LLM"
    ) -> Generator[str, None, str]:
        """Stream response tokens from Ollama or Groq."""
        start = time.time()
        if self.provider == "groq" and self.groq_api_key:
            return self._generate_stream_groq(prompt, system, temperature, format_json, agent_name, start)
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature
            }
        }
        if system:
            payload["system"] = system
        if format_json:
            payload["format"] = "json"

        accumulated = []
        with httpx.stream("POST", f"{self.base_url}/api/generate", json=payload, timeout=90.0) as r:
            for line in r.iter_lines():
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                    token = chunk.get("response", "")
                    if token:
                        accumulated.append(token)
                        yield token
                    if chunk.get("done", False):
                        break
                except Exception:
                    continue

        full_response = "".join(accumulated)
        duration = time.time() - start
        self.log_call(agent_name, prompt, full_response, duration, self.model, {"system": system, "stream": True})
        return full_response

    def generate_json_with_retry(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.3,
        schema_cls: Optional[Any] = None,
        agent_name: str = "LLM",
        max_retries: int = 2,
        num_predict: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate structured JSON with automatic repair and retry loops."""
        cur_prompt = prompt
        attempts = 0

        while attempts <= max_retries:
            raw_response = self.generate(
                prompt=cur_prompt,
                system=system,
                temperature=temperature,
                format_json=True,
                agent_name=agent_name,
                num_predict=num_predict
            )

            cleaned = self.clean_json_text(raw_response)
            try:
                data = json.loads(cleaned)
                if schema_cls:
                    # Validate against Pydantic schema
                    parsed = schema_cls.model_validate(data)
                    return parsed.model_dump()
                return data
            except Exception as parse_err:
                attempts += 1
                if attempts > max_retries:
                    # Final attempt: try basic fallback extraction
                    raise ValueError(f"Failed to generate valid JSON after {max_retries} retries. Error: {parse_err}\nRaw text: {raw_response}")
                # Append strict correction prompt
                cur_prompt = (
                    f"{prompt}\n\n"
                    f"[ERROR]: Your previous response was invalid JSON or violated schema: {parse_err}.\n"
                    f"Return ONLY valid RFC-8259 JSON matching the required schema without any explanation or markdown formatting."
                )
