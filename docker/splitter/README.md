# Audio Splitter Service

Simple FastAPI service that accepts an audio file, splits it into chunks (no overlap), and returns base64-encoded parts with timestamps. Useful for preparing longer inputs for speech-to-text APIs limited by file size/duration.

Note: v2.0.0 removes the `overlap_ms` parameter and field from the API.

## Endpoint

- POST `/split`
  - form-data:
    - `file` (required): audio file (mp3, wav, m4a, ogg, flac, webm, mp4, aac)
    - `chunk_ms` (optional, default 540000): chunk size in ms (9 minutes)
    - `output_format` (optional, default `mp3`): one of mp3|wav|ogg|flac|m4a

Response JSON:

```json
{
  "filename": "input.mp3",
  "duration_ms": 123456,
  "chunk_ms": 540000,
  "count": 3,
  "chunks": [
    {
      "index": 0,
      "start_ms": 0,
      "end_ms": 540000,
      "format": "mp3",
      "content_base64": "..."
    }
  ]
}
```

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
  -F "chunk_ms=540000" \
  -F "output_format=mp3" \
  http://localhost:8083/split > result.json
```

This image includes ffmpeg for broad codec support via pydub.




