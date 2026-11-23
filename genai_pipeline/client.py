"""
Thin, provider-agnostic wrapper. Swap providers via config.settings.genai_provider
without touching pipeline.py — the pipeline only ever calls GenAIClient.complete().
"""
import json
import time
from pathlib import Path

from config.settings import get_settings

PROMPT_DIR = Path(__file__).parent / "prompt_templates"


def load_prompt_template(name: str = "complaint_analysis_v1") -> str:
    return (PROMPT_DIR / f"{name}.txt").read_text()


class GenAIError(Exception):
    pass


class GenAIClient:
    def __init__(self):
        self.settings = get_settings()

    def complete_json(self, prompt: str, json_schema: dict, max_retries: int | None = None) -> dict:
        """Calls the configured provider and returns a parsed JSON dict.
        Retries on parse/API failure with backoff; raises GenAIError after
        max_retries so the caller can route to manual review instead of
        looping forever."""
        max_retries = max_retries or self.settings.genai_max_retries
        last_error: Exception | None = None

        for attempt in range(max_retries):
            try:
                raw_text = self._call_provider(prompt, json_schema)
                return json.loads(raw_text)
            except Exception as exc:  # noqa: BLE001 — deliberately broad, we retry/raise
                last_error = exc
                time.sleep(min(2 ** attempt, 8))

        raise GenAIError(f"GenAI call failed after {max_retries} attempts: {last_error}")

    def _call_provider(self, prompt: str, json_schema: dict) -> str:
        provider = self.settings.genai_provider
        if provider == "anthropic":
            return self._call_anthropic(prompt, json_schema)
        raise GenAIError(f"Provider '{provider}' not wired up yet — add a _call_<provider> method")

    def _call_anthropic(self, prompt: str, json_schema: dict) -> str:
        import anthropic

        client = anthropic.Anthropic(api_key=self.settings.anthropic_api_key)
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            tools=[{
                "name": "return_complaint_analysis",
                "description": "Return the structured complaint analysis.",
                "input_schema": json_schema,
            }],
            tool_choice={"type": "tool", "name": "return_complaint_analysis"},
            messages=[{"role": "user", "content": prompt}],
        )
        for block in response.content:
            if block.type == "tool_use":
                import json as _json
                return _json.dumps(block.input)
        raise GenAIError("No tool_use block in Anthropic response")
