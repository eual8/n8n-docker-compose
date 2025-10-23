# Whisper.cpp Audio Transcription Service

Сервис транскрипции аудио на основе [whisper.cpp](https://github.com/ggerganov/whisper.cpp) - оптимизированной C++ реализации OpenAI Whisper.

## Особенности

- Быстрая транскрипция благодаря C++ реализации
- Совместимый API с оригинальным Whisper сервисом
- Поддержка множества аудио форматов: MP3, WAV, M4A, OGG, FLAC, WebM, MP4
- Автоматическое скачивание моделей при первом использовании
- Поддержка нескольких моделей (tiny, base, small, medium, large)

## API Endpoints

### POST /transcribe

Транскрибирует аудио файл.

**Параметры:**
- `file` (required): Аудио файл
- `model` (optional): Название модели (по умолчанию "base")
  - Доступные: tiny, base, small, medium, large
- `language` (optional): Код языка (например "ru", "en")
- `task` (optional): "transcribe" или "translate" (по умолчанию "transcribe")

**Пример:**
```bash
curl -X POST -F "file=@audio.mp3" -F "model=base" -F "language=ru" http://localhost:8083/transcribe
```

**Ответ:**
```json
{
  "text": "Полный транскрибированный текст",
  "language": "ru",
  "language_probability": 0.99,
  "duration": 10.5,
  "segments": [
    {
      "start": 0.0,
      "end": 2.5,
      "text": "Первый сегмент"
    }
  ],
  "model": "base"
}
```

### GET /health

Проверка статуса сервиса.

**Ответ:**
```json
{
  "status": "healthy",
  "service": "whisper-cpp",
  "whisper_cpp_available": true
}
```

### GET /models

Список доступных моделей.

### GET /info

Информация о сервисе и доступных endpoints.

## Модели

- **tiny** (~75 MB): Самая быстрая, наименее точная
- **base** (~142 MB): Базовая модель, хороший баланс
- **small** (~466 MB): Улучшенная точность
- **medium** (~1.5 GB): Высокая точность
- **large** (~2.9 GB): Максимальная точность

Модели скачиваются автоматически при первом использовании и кэшируются в volume.

## Использование в Docker Compose

```yaml
whisper-cpp:
  build:
    context: ./docker/whisper-cpp
    dockerfile: Dockerfile
  container_name: whisper-cpp
  restart: unless-stopped
  ports:
    - "8083:8083"
  environment:
    - PYTHONUNBUFFERED=1
  volumes:
    - whisper_cpp_models:/models
    - whisper_cpp_cache:/tmp/whisper
```

## Отличия от оригинального Whisper

- Использует whisper.cpp вместо faster-whisper
- Работает на CPU эффективнее благодаря оптимизированной C++ реализации
- API полностью совместим с оригинальным сервисом
- Порт по умолчанию: 8083 (вместо 8082)

## Требования

- Docker
- FFmpeg (включен в образ)
- ~2-4 GB RAM (зависит от модели)
