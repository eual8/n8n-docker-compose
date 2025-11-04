from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydub import AudioSegment
from typing import List, Optional
import base64
import io
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Audio Splitter API",
    description="Upload an audio file and receive chunked parts.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPPORTED_EXT = {"mp3", "wav", "m4a", "ogg", "flac", "webm", "mp4", "aac"}


def export_segment_to_bytes(segment: AudioSegment, fmt: str) -> bytes:
    buf = io.BytesIO()
    params = {}
    # Favor safe defaults
    if fmt == "mp3":
        params = {"bitrate": "192k"}
    try:
        segment.export(buf, format=fmt, **params)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {e}")
    return buf.getvalue()


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "splitter"}


@app.post("/split")
async def split_audio(
    file: UploadFile = File(..., description="Audio file to split"),
    chunk_ms: int = Form(540_000, description="Chunk size in milliseconds (default 9 minutes)"),
    output_format: str = Form("mp3", description="Output format for chunks: mp3|wav|ogg|flac|m4a"),
):
    # Validate
    if chunk_ms <= 0:
        raise HTTPException(status_code=400, detail="chunk_ms must be > 0")

    filename = file.filename or "audio"
    ext = (filename.rsplit(".", 1)[-1].lower() if "." in filename else "").strip()
    if ext and ext not in SUPPORTED_EXT:
        raise HTTPException(status_code=400, detail=f"Unsupported file extension: {ext}")

    try:
        # Read into memory
        data = await file.read()
        if not data:
            raise HTTPException(status_code=400, detail="Empty file")

        # Let pydub/ffmpeg detect format from bytes
        audio = AudioSegment.from_file(io.BytesIO(data))
        duration_ms = len(audio)

        chunks: List[dict] = []
        start = 0
        index = 0
        # Sliding window without overlap
        while start < duration_ms:
            end = min(start + chunk_ms, duration_ms)
            segment = audio[start:end]
            raw = export_segment_to_bytes(segment, output_format)
            b64 = base64.b64encode(raw).decode("ascii")
            chunks.append({
                "index": index,
                "start_ms": start,
                "end_ms": end,
                "format": output_format,
                "content_base64": b64,
            })
            index += 1
            if end >= duration_ms:
                break
            start = end

        return {
            "filename": filename,
            "duration_ms": duration_ms,
            "chunk_ms": chunk_ms,
            "count": len(chunks),
            "chunks": chunks,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to split audio")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8083)



