# YT-DLP Service

Сервис для скачивания видео с YouTube и других платформ с использованием yt-dlp.

## 🔧 Последнее обновление

**Дата:** 23 октября 2025  
**Изменения:**
- ✅ Обновлен yt-dlp до версии 2024.10.22
- ✅ Добавлены параметры обхода блокировок YouTube
- ✅ Добавлен User-Agent для стабильной работы
- ✅ Исправлена ошибка HTTP 403 Forbidden

### Решённые проблемы

**Проблема:** `ERROR: unable to download video data: HTTP Error 403: Forbidden`

**Решение:**
1. Обновлена версия yt-dlp (YouTube регулярно меняет защиту)
2. Добавлены параметры `extractor_args` с клиентом iOS/web
3. Добавлен современный User-Agent браузера

## Возможности

- 🎥 Скачивание видео в различных качествах
- 🎵 Извлечение аудио в формате MP3
- 📝 Получение информации о видео без скачивания
- 📄 Получение субтитров/транскриптов
- 🌐 REST API для интеграции с n8n и другими системами

## API Endpoints

### 1. Проверка здоровья сервиса

```bash
GET /health
```

**Ответ:**
```json
{
  "status": "healthy",
  "service": "yt-dlp"
}
```

### 2. Получение информации о видео

```bash
POST /info
Content-Type: application/json

{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID"
}
```

**Ответ:**
```json
{
  "title": "Название видео",
  "description": "Описание",
  "duration": 300,
  "uploader": "Автор канала",
  "upload_date": "20231015",
  "view_count": 1000000,
  "like_count": 50000,
  "thumbnail": "https://...",
  "formats": [...]
}
```

### 3. Скачивание видео/аудио

```bash
POST /download
Content-Type: application/json

{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "format": "video",  // "video", "audio", или "best"
  "quality": "1080p"  // "best", "1080p", "720p", и т.д.
}
```

**Примеры:**

Скачать видео в лучшем качестве:
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "format": "video",
  "quality": "best"
}
```

Скачать только аудио в MP3:
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "format": "audio"
}
```

**Ответ:**
```json
{
  "status": "success",
  "filename": "video_title.mp4",
  "path": "/downloads/video_title.mp4",
  "title": "Название видео"
}
```

### 4. Получение субтитров

```bash
POST /download-transcript
Content-Type: application/json

{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "lang": "en"  // код языка (en, ru, es, и т.д.)
}
```

**Ответ:**
```json
{
  "status": "success",
  "subtitles": {
    "manual": [...],
    "automatic": [...]
  },
  "title": "Название видео"
}
```

## Использование с n8n

1. Используйте ноду **HTTP Request** для отправки запросов к API
2. URL сервиса: `http://ytdlp:8081`
3. Примеры запросов см. выше

### Пример n8n workflow для скачивания видео:

1. **Trigger** (вебхук или расписание)
2. **HTTP Request** к `http://ytdlp:8081/info` для получения информации
3. **HTTP Request** к `http://ytdlp:8081/download` для скачивания
4. Обработка результата

## Поддерживаемые платформы

yt-dlp поддерживает более 1000 сайтов, включая:
- YouTube
- Vimeo
- Dailymotion
- Facebook
- Instagram
- Twitter
- TikTok
- И многие другие

Полный список: https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md

## Тестирование

Проверка работы сервиса:

```bash
# Проверка здоровья
curl http://localhost:8081/health

# Получение информации о видео
curl -X POST http://localhost:8081/info \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'

# Скачивание аудио
curl -X POST http://localhost:8081/download \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "format": "audio"}'
```

## Volumes

- `/downloads` - директория для сохранения скачанных файлов
- `/root/.cache` - кэш yt-dlp

## Порты

- `8081` - HTTP API сервер

## Переменные окружения

- `PYTHONUNBUFFERED=1` - вывод логов Python без буферизации
