from fastapi import APIRouter, HTTPException, Request
from packages.services.voice_service import voice_service

router = APIRouter()

@router.post("/stt")
async def speech_to_text(request: Request):
    audio_data = await request.body()
    if len(audio_data) > voice_service.max_upload_bytes:
        raise HTTPException(status_code=413, detail="Payload too large")
    
    text = voice_service.transcribe(audio_data)
    return {"text": text}

@router.get("/tts")
async def text_to_speech(text: str):
    audio_bytes = voice_service.speak(text)
    return {"status": "success", "audio_len": len(audio_bytes)}
