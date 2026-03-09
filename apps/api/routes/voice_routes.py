from fastapi import APIRouter, HTTPException, Request
from packages.services.voice_service import voice_service

from apps.api.response_models import SuccessResponse

router = APIRouter()

@router.post("/stt", response_model=SuccessResponse)
async def speech_to_text(request: Request):
    audio_data = await request.body()
    if len(audio_data) > voice_service.max_upload_bytes:
        raise HTTPException(status_code=413, detail="Payload too large")
    
    text = voice_service.transcribe(audio_data)
    return SuccessResponse(data={"text": text})

@router.get("/tts", response_model=SuccessResponse)
async def text_to_speech(text: str):
    audio_bytes = voice_service.speak(text)
    return SuccessResponse(data={"audio_len": len(audio_bytes)})
