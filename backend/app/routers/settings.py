from fastapi import APIRouter, Depends, HTTPException, status
from google import genai

from backend.app.models import User
from backend.app.routers.auth import get_current_user
from backend.app.schemas import GeminiSettingsRequest, GeminiSettingsResponse
from backend.services.app_settings import (
    clear_gemini_api_key,
    is_gemini_api_key_configured,
    get_gemini_api_key,
    save_gemini_api_key,
)

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/gemini", response_model=GeminiSettingsResponse)
def get_gemini_settings(current_user: User = Depends(get_current_user)) -> GeminiSettingsResponse:
    return GeminiSettingsResponse(configured=is_gemini_api_key_configured())


@router.put("/gemini", response_model=GeminiSettingsResponse)
def put_gemini_settings(request: GeminiSettingsRequest, current_user: User = Depends(get_current_user)) -> GeminiSettingsResponse:
    api_key = request.api_key.strip()
    if not api_key:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="API key is required")
    try:
        genai.Client(api_key=api_key)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="That Gemini API key could not be initialized") from exc
    save_gemini_api_key(api_key)
    return GeminiSettingsResponse(configured=True)


@router.delete("/gemini", response_model=GeminiSettingsResponse)
def delete_gemini_settings(current_user: User = Depends(get_current_user)) -> GeminiSettingsResponse:
    clear_gemini_api_key()
    return GeminiSettingsResponse(configured=False)
