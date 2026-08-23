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

    def get_status_info(self) -> dict:
        if not self.api_key or not self.api_key.strip():
            return {"configured": False, "status": "missing_api_key"}

        val = self.api_key.strip()
        lower_val = val.lower()
        placeholders = ["your", "placeholder", "enter", "<", ">", "dummy", "api_key"]

        if any(p in lower_val for p in placeholders):
            return {"configured": False, "status": "invalid_api_key"}

        if len(val) < 20:
            return {"configured": False, "status": "invalid_api_key"}

        if not self.client:
            return {"configured": False, "status": "invalid_api_key"}

        # Attempt to get the model details to verify the key and provider are actually usable
        try:
            self.client.models.get(model=self.model)
            return {"configured": True, "status": "ready"}
        except (genai_errors.APIError, genai_errors.ClientError) as e:
            error_str = str(e).lower()
            if (
                "api key" in error_str
                or "api_key" in error_str
                or "invalid_argument" in error_str
                or "permission" in error_str
                or "unauthenticated" in error_str
                or "forbidden" in error_str
            ):
                return {"configured": False, "status": "invalid_api_key"}
            elif "not_found" in error_str or "model" in error_str:
                return {
                    "configured": False,
                    "status": "unavailable",
                }  # model unavailable
            else:
                return {
                    "configured": False,
                    "status": "unavailable",
                }  # generic provider failure
        except Exception:  # noqa: BLE001
            return {"configured": False, "status": "unavailable"}

    def is_configured(self) -> bool:
        return self.get_status_info()["configured"]

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
        except (genai_errors.APIError, genai_errors.ClientError) as e:
            error_str = str(e).lower()
            if (
                "api key" in error_str
                or "api_key" in error_str
                or "invalid_argument" in error_str
            ):
                logger.error("Gemini API Error: Invalid API Key")
                raise RuntimeError("AI provider error: Invalid API Key")
            if "not_found" in error_str or "model" in error_str:
                logger.error("Gemini API Error: Invalid Model")
                raise RuntimeError("AI provider error: Invalid Model")
            logger.error("Gemini API Error: External provider failure")
            raise RuntimeError("AI provider error: External provider failure")
        except Exception:  # noqa: BLE001
            logger.error("Unexpected error calling Gemini API")
            raise RuntimeError(
                "An unexpected error occurred while communicating with the AI provider."
            )
