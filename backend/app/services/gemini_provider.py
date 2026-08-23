import logging

from google import genai
from google.genai import errors as genai_errors

from app.core.config import settings

logger = logging.getLogger(__name__)


class GeminiProvider:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model = settings.GEMINI_MODEL
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def generate_text(self, prompt: str) -> str:
        if not self.is_configured():
            logger.error("Gemini API key is not configured.")
            raise ValueError("AI provider is not configured.")

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
            if not response.text:
                raise ValueError("Empty response from AI provider.")
            return response.text
        except genai_errors.APIError as e:
            logger.error(f"Gemini API Error: {e!s}")
            raise RuntimeError(f"AI provider error: {e!s}")
        except Exception as e:  # noqa: BLE001
            logger.error(f"Unexpected error calling Gemini API: {e!s}")
            raise RuntimeError(
                "An unexpected error occurred while communicating with the AI provider."
            )
