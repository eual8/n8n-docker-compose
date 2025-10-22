# Whisper Audio Transcription Service

API сервис для транскрипции аудио файлов с использованием OpenAI Whisper через faster-whisper (оптимизированная версия на базе CTranslate2).

## Возможности

- Транскрипция аудио в текст
- Поддержка множества форматов: MP3, WAV, M4A, OGG, FLAC, WebM
- Автоматическое определение языка
- Опциональный перевод на английский
- Временные метки для каждого сегмента
- Выбор модели (tiny, base, small, medium, large)

## API Endpoints

### 1. Health Check
```bash
GET /health
```

Проверка статуса сервиса.

**Ответ:**
```json
{
  "status": "healthy",
  "service": "faster-whisper",
  "model_loaded": true,
  "current_model": "base"
}
```

### 2. Транскрипция аудио
```bash
POST /transcribe
```

Транскрибирует аудио файл в текст.

**Параметры (multipart/form-data):**
- `file` (required): Аудио файл (MP3, WAV, M4A, OGG, FLAC, WebM)
- `model` (optional): Модель Whisper (tiny/base/small/medium/large), по умолчанию 'base'
- `language` (optional): Код языка (ru, en, fr, и т.д.), автоопределение если не указан
- `translate` (optional): Перевести на английский (true/false), по умолчанию false

**Пример запроса (curl):**
```bash
# Базовая транскрипция
curl -X POST http://localhost:8082/transcribe \
  -F "file=@audio.mp3"

# С указанием модели и языка
curl -X POST http://localhost:8082/transcribe \
  -F "file=@audio.mp3" \
  -F "model=small" \
  -F "language=ru"

# С переводом на английский
curl -X POST http://localhost:8082/transcribe \
  -F "file=@audio.mp3" \
  -F "translate=true"
```

**Ответ:**
```json
{
  "text": "Полный транскрибированный текст...",
  "language": "ru",
  "model": "base",
  "segments": [
    {
      "start": 0.0,
      "end": 5.2,
      "text": "Первый сегмент текста"
    },
    {
      "start": 5.2,
      "end": 10.8,
      "text": "Второй сегмент текста"
    }
  ]
}
```

### 3. Список моделей
```bash
GET /models
```

Получить список доступных моделей Whisper.

**Ответ:**
```json
{
  "models": [
    {
      "name": "tiny",
      "size": "~75 MB",
      "description": "Самая быстрая, наименее точная"
    },
    {
      "name": "base",
      "size": "~142 MB",
      "description": "Базовая модель (по умолчанию)"
    },
    ...
  ]
}
```

### 4. Информация о сервисе
```bash
GET /info
```

Получить информацию о сервисе и доступных endpoints.

## Использование в n8n

### HTTP Request Node
1. Method: POST
2. URL: `http://whisper:8082/transcribe`
3. Body: Form-Data
   - Добавьте поле `file` с типом "Binary Data"
   - Опционально добавьте поля `model`, `language`, `translate`

### Пример workflow
```
[Trigger] → [Read Binary File] → [HTTP Request to Whisper] → [Process Text]
```

## Модели Whisper

| Модель | Размер | Скорость | Точность | Рекомендация |
|--------|--------|----------|----------|--------------|
| tiny   | ~75 MB | Очень быстро | Базовая | Для быстрых тестов |
| base   | ~142 MB | Быстро | Хорошая | По умолчанию |
| small  | ~466 MB | Средне | Очень хорошая | Рекомендуется |
| medium | ~1.5 GB | Медленно | Отличная | Для высокой точности |
| large  | ~2.9 GB | Очень медленно | Лучшая | Для максимальной точности |

## Поддерживаемые языки

Whisper поддерживает 99+ языков, включая:
- Русский (ru)
- Английский (en)
- Испанский (es)
- Французский (fr)
- Немецкий (de)
- Китайский (zh)
- Японский (ja)
- И многие другие...

## Примеры использования

### Python
```python
import requests

# Транскрипция файла
with open('audio.mp3', 'rb') as f:
    files = {'file': f}
    data = {'model': 'base', 'language': 'ru'}
    response = requests.post('http://localhost:8082/transcribe', 
                           files=files, data=data)
    result = response.json()
    print(result['text'])
```

### JavaScript/Node.js
```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

const form = new FormData();
form.append('file', fs.createReadStream('audio.mp3'));
form.append('model', 'base');
form.append('language', 'ru');

axios.post('http://localhost:8082/transcribe', form, {
    headers: form.getHeaders()
})
.then(response => {
    console.log(response.data.text);
})
.catch(error => {
    console.error(error);
});
```

## Требования

- Docker
- Минимум 2GB RAM (больше для больших моделей)
- При первом запуске модель будет загружена автоматически

## Логи и отладка

Для просмотра логов контейнера:
```bash
docker logs whisper
```

Для интерактивного просмотра:
```bash
docker logs -f whisper
```

## Ограничения

- Максимальный размер файла зависит от настроек Flask (по умолчанию 16MB)
- Время обработки зависит от:
  - Длительности аудио
  - Выбранной модели
  - Доступных ресурсов CPU/GPU

## Troubleshooting

### Модель не загружается
- Убедитесь, что достаточно места на диске
- Проверьте интернет-соединение (для первой загрузки)
- Попробуйте использовать модель меньшего размера

### Ошибка "Out of memory"
- Используйте модель меньшего размера (tiny или base)
- Увеличьте RAM для Docker контейнера

### Медленная обработка
- Используйте модель меньшего размера
- Убедитесь, что контейнер имеет доступ к достаточным ресурсам CPU
