import os
from dotenv import load_dotenv

load_dotenv(".env")
from app.core.config import settings
print("Model:", settings.GEMINI_MODEL)

from app.services.gemini_provider import GeminiProvider
ai = GeminiProvider()
print("Status:", ai.get_status_info())
