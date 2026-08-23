import logging

from app.services.gemini_provider import GeminiProvider

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self):
        self.provider = GeminiProvider()

    def get_status(self) -> dict:
        configured = self.provider.is_configured()
        return {
            "provider": "gemini",
            "model": self.provider.model,
            "configured": configured,
            "status": "ready" if configured else "unconfigured",
        }

    def generate(self, prompt: str) -> dict:
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        try:
            response_text = self.provider.generate_text(prompt)
            return {
                "response": response_text,
                "model": self.provider.model,
                "status": "success",
            }
        except ValueError:
            raise
        except RuntimeError:
            raise
        except Exception as e:  # noqa: BLE001
            logger.error(f"AIService error: {e!s}")
            raise RuntimeError("Failed to generate AI response.")
