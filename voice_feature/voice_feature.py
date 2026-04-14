import asyncio
import edge_tts
from typing import List

EDGE_TTS_RATE = "+0%"
EDGE_TTS_VOLUME = "+0%"
EDGE_TTS_PITCH = "+0Hz"

async def synthesize_speech(text: str, voice: str) -> bytes:
    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=EDGE_TTS_RATE,
        volume=EDGE_TTS_VOLUME,
        pitch=EDGE_TTS_PITCH,
    )
    chunks: List[bytes] = []
    async for chunk in communicate.stream():
        if chunk.get("type") == "audio":
            chunks.append(chunk["data"])
    return b"".join(chunks)
