from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydub import AudioSegment
from typing import List
from datetime import datetime
from pathlib import Path
import io
import logging
import os
import re
import uuid

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

# Configure output directories via environment for docker-compose flexibility.
OUTPUT_ROOT = Path(os.environ.get("SPLITTER_OUTPUT_ROOT", "/shared/splitter")).expanduser()
PUBLIC_ROOT = Path(os.environ.get("SPLITTER_PUBLIC_ROOT", str(OUTPUT_ROOT))).expanduser()

# Lazily create the root directory so container start doesn't fail if volume missing.
try:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
except Exception as exc:  # pragma: no cover - protects startup when volume misconfigured
    logger.error("Unable to create output root %s: %s", OUTPUT_ROOT, exc)
    raise

SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


def _slugify(stem: str) -> str:
    cleaned = SAFE_FILENAME_RE.sub("_", stem).strip("._")
    return cleaned or "audio"


def allocate_output_directory(original_filename: str) -> tuple[Path, Path, str]:
    """Create a unique directory for the request and return (absolute, relative, stem)."""
    stem = _slugify(Path(original_filename).stem or "audio")
    now = datetime.utcnow()
    relative_dir = Path(now.strftime("%Y/%m/%d")) / f"{stem}_{now.strftime('%H%M%S')}_{uuid.uuid4().hex[:8]}"
    target_dir = OUTPUT_ROOT / relative_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir, relative_dir, stem


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
    chunk_ms: int = Form(360_000, description="Chunk size in milliseconds (default 6 minutes)"),
    overlap_ms: int = Form(5_000, description="Overlap between chunks in milliseconds"),
    output_format: str = Form("mp3", description="Output format for chunks: mp3|wav|ogg|flac|m4a"),
):
    # Validate
    if chunk_ms <= 0:
        raise HTTPException(status_code=400, detail="chunk_ms must be > 0")
    if overlap_ms < 0:
        raise HTTPException(status_code=400, detail="overlap_ms must be >= 0")
    if overlap_ms >= chunk_ms:
        raise HTTPException(status_code=400, detail="overlap_ms must be smaller than chunk_ms")

    filename = file.filename or "audio"
    ext = (filename.rsplit(".", 1)[-1].lower() if "." in filename else "").strip()
    if ext and ext not in SUPPORTED_EXT:
        raise HTTPException(status_code=400, detail=f"Unsupported file extension: {ext}")

    output_format = output_format.strip().lower()
    if output_format not in SUPPORTED_EXT:
        raise HTTPException(status_code=400, detail=f"Unsupported output format: {output_format}")

    try:
        # Read into memory
        data = await file.read()
        if not data:
            raise HTTPException(status_code=400, detail="Empty file")

        # Let pydub/ffmpeg detect format from bytes
        audio = AudioSegment.from_file(io.BytesIO(data))
        duration_ms = len(audio)

        request_dir, relative_dir, stem = allocate_output_directory(filename)
        logger.info("Writing %s chunks to %s", filename, request_dir)

        chunks: List[dict] = []
        start = 0
        index = 0
        # Sliding window with configurable overlap
        while start < duration_ms:
            end = min(start + chunk_ms, duration_ms)
            segment = audio[start:end]
            raw = export_segment_to_bytes(segment, output_format)
            chunk_name = f"{stem}_chunk_{index:03d}.{output_format}"
            chunk_path = request_dir / chunk_name
            try:
                with chunk_path.open("wb") as fh:
                    fh.write(raw)
            except Exception as exc:
                logger.exception("Failed writing chunk %s", chunk_path)
                raise HTTPException(status_code=500, detail=f"Failed to write chunk: {exc}")

            relative_chunk = relative_dir / chunk_name
            public_path = (PUBLIC_ROOT / relative_chunk).as_posix()

            chunks.append({
                "index": index,
                "start_ms": start,
                "end_ms": end,
                "format": output_format,
                "path": public_path,
                "filename": chunk_name,
                "size_bytes": len(raw),
            })
            index += 1
            if end >= duration_ms:
                break
            # Следующий фрагмент начинается с учетом пересечения
            start = end - overlap_ms

        return {
            "filename": filename,
            "duration_ms": duration_ms,
            "chunk_ms": chunk_ms,
            "overlap_ms": overlap_ms,
            "count": len(chunks),
            "output_directory": (PUBLIC_ROOT / relative_dir).as_posix(),
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



