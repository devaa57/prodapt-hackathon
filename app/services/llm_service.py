"""
Centralised Gemini LLM service.

Every agent routes through this single service so that configuration,
retries, and rate-limit handling live in one place.
"""

from __future__ import annotations

import json
import logging
import os
from typing import TypeVar, Type

from google import genai
from google.genai import types
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMService:
    """Thin wrapper around the google-genai SDK."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-2.0-flash",
    ) -> None:
        resolved_key = api_key or os.getenv("GEMINI_API_KEY", "")
        if not resolved_key:
            raise ValueError(
                "GEMINI_API_KEY is not set. "
                "Pass it explicitly or set the environment variable."
            )
        self.client = genai.Client(api_key=resolved_key)
        self.model = model

    # ── structured output ──────────────────────────────────────────

    def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_schema: Type[T],
        temperature: float = 0.1,
        max_retries: int = 2,
    ) -> T:
        """
        Call Gemini with a JSON-mode response schema and validate
        the result against *response_schema*.

        On validation failure the prompt is retried with the error
        message appended so the model can self-correct.
        """
        last_error: str | None = None

        for attempt in range(max_retries + 1):
            try:
                prompt = user_prompt
                if last_error and attempt > 0:
                    prompt += (
                        f"\n\n[SYSTEM] Your previous response had a validation error:\n"
                        f"{last_error}\n"
                        f"Please correct the JSON output to match the required schema."
                    )

                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        response_mime_type="application/json",
                        response_schema=response_schema,
                        temperature=temperature,
                    ),
                )

                raw_text = response.text
                if not raw_text:
                    raise ValueError("Gemini returned an empty response.")

                result = response_schema.model_validate_json(raw_text)
                return result

            except ValidationError as exc:
                last_error = str(exc)
                logger.warning(
                    "Schema validation failed (attempt %d/%d): %s",
                    attempt + 1,
                    max_retries + 1,
                    last_error,
                )
                if attempt == max_retries:
                    raise ValueError(
                        f"LLM output failed schema validation after "
                        f"{max_retries + 1} attempts:\n{last_error}"
                    ) from exc

            except Exception as exc:
                logger.error("LLM call failed (attempt %d/%d): %s", attempt + 1, max_retries + 1, exc)
                if attempt == max_retries:
                    raise
                last_error = str(exc)

        # Should be unreachable, but satisfy type checkers.
        raise RuntimeError("generate_structured: exhausted retries without result")

    # ── plain text (for report narrative) ──────────────────────────

    def generate_text(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
    ) -> str:
        """Return a plain-text response (no schema enforcement)."""
        response = self.client.models.generate_content(
            model=self.model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=temperature,
            ),
        )
        return response.text or ""
