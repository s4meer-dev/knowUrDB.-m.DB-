from app.models.ai import AIGenerateRequest, AIGenerateResponse, AIStatusResponse
from app.services.ai_service import AIService
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter()


def get_ai_service() -> AIService:
    return AIService()


@router.get("/status", response_model=AIStatusResponse)
def get_ai_status(ai_service: AIService = Depends(get_ai_service)):  # noqa: B008
    """Get the current configuration status of the AI service."""
    status_dict = ai_service.get_status()
    return AIStatusResponse(**status_dict)


@router.post("/generate", response_model=AIGenerateResponse)
def generate_ai_response(
    request: AIGenerateRequest,
    ai_service: AIService = Depends(get_ai_service),  # noqa: B008
):
    """Generate a response from the AI based on the provided prompt."""
    if not request.prompt or not request.prompt.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prompt cannot be empty or whitespace-only.",
        )

    try:
        response_dict = ai_service.generate(request.prompt)
        return AIGenerateResponse(**response_dict)
    except ValueError as e:
        # e.g. "AI provider is not configured."
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        )
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except Exception:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during AI generation.",
        )
