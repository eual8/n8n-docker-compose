# Audio Splitter Service

Simple FastAPI service that accepts an audio file, splits it into chunks (with configurable overlap), and writes the pieces to disk. The API responds with filesystem paths (instead of base64 payloads) so that downstream services such as n8n can read the generated files directly from a shared volume.

Note: As of v2.0.0 the API accepts an `overlap_ms` form parameter to control how much each chunk overlaps the next one (in milliseconds).

## Endpoint

- POST `/split`
  - form-data:
    - `file` (required): audio file (mp3, wav, m4a, ogg, flac, webm, mp4, aac)
    - `chunk_ms` (optional, default 360000): chunk size in ms (6 minutes)
    - `overlap_ms` (optional, default 5000): overlap between chunks in ms (default 5 seconds)
    - `output_format` (optional, default `mp3`): one of mp3|wav|ogg|flac|m4a

Response JSON:

```json
{
  "filename": "input.mp3",
  "duration_ms": 123456,
  "chunk_ms": 360000,
  "overlap_ms": 5000,
  "count": 3,
  "output_directory": "/shared/splitter/input_20240918T104455_ab12cd34",
  "chunks": [
    {
      "index": 0,
      "start_ms": 0,
      "end_ms": 540000,
      "format": "mp3",
      "filename": "input_chunk_000.mp3",
      "path": "/shared/splitter/input_20240918T104455_ab12cd34/input_chunk_000.mp3",
      "size_bytes": 1234567
    }
  ]
}
```

All files are created beneath the directory defined by the `SPLITTER_OUTPUT_ROOT` environment variable (defaults to `/shared/splitter`). Every request gets its own dated subdirectory to avoid name collisions and keep related chunks together.

## Docker

Build and run locally:

```bash
docker build -t splitter:local .
docker run --rm -p 8083:8083 splitter:local
```

Test:

```bash
curl -X POST \
  -F "file=@sample.mp3" \
  -F "chunk_ms=360000" \
  -F "overlap_ms=5000" \
  -F "output_format=mp3" \
  http://localhost:8083/split > result.json
```

This image includes ffmpeg for broad codec support via pydub.

### Sharing files with n8n

When running via `docker-compose`, mount a shared named volume into both the `splitter` and `n8n` services. The splitter writes chunks to `/shared/splitter`, while n8n mounts the same volume (read-only) at `/shared` to consume the generated files. Adjust `SPLITTER_PUBLIC_ROOT` if n8n needs to use a different mount point in its container.




