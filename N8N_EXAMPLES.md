# Примеры использования YT-DLP в n8n

## Пример 1: Простое скачивание аудио

### Workflow:
1. **Manual Trigger** - ручной запуск
2. **Set** - установить URL видео
3. **HTTP Request** - вызов YT-DLP API
4. **IF** - проверка успешности
5. **Code** - обработка результата

### HTTP Request настройки:
```
Method: POST
URL: http://ytdlp:8081/download
Body Type: JSON

JSON Body:
{
  "url": "{{ $json.videoUrl }}",
  "format": "audio"
}
```

---

## Пример 2: Получение метаданных и индексация в Elasticsearch

### Workflow:
1. **Webhook** - получение URL от пользователя
2. **HTTP Request** - получить информацию о видео
   - URL: `http://ytdlp:8081/info`
   - Method: POST
   - Body: `{"url": "{{ $json.body.url }}"}`

3. **Set** - подготовить данные для Elasticsearch
   ```
   title: {{ $json.title }}
   description: {{ $json.description }}
   duration: {{ $json.duration }}
   uploader: {{ $json.uploader }}
   views: {{ $json.view_count }}
   ```

4. **HTTP Request** - индексировать в Elasticsearch
   - URL: `http://elasticsearch:9200/videos/_doc`
   - Method: POST
   - Body: данные из предыдущего шага

---

## Пример 3: Скачивание плейлиста

### Workflow:
1. **Webhook** - получить URL плейлиста
2. **HTTP Request** - получить информацию о плейлисте
3. **Split In Batches** - обработать по одному видео
4. **HTTP Request** - скачать каждое видео
5. **Wait** - пауза между запросами
6. **Merge** - объединить результаты

---

## Пример 4: Автоматическое скачивание новых видео с канала

### Workflow:
1. **Schedule** - запуск каждый час
2. **HTTP Request** - получить последние видео канала
3. **Function** - фильтровать новые видео
4. **Loop Over Items** - для каждого нового видео:
   - Получить метаданные
   - Скачать аудио
   - Сохранить в базе данных
   - Отправить уведомление

---

## Пример 5: Транскрипция видео с помощью Ollama

### Workflow:
1. **Webhook** - получить URL видео
2. **HTTP Request** - скачать аудио через YT-DLP
   ```json
   {
     "url": "{{ $json.videoUrl }}",
     "format": "audio"
   }
   ```

3. **HTTP Request** - получить субтитры
   ```json
   {
     "url": "{{ $json.videoUrl }}",
     "lang": "en"
   }
   ```

4. **HTTP Request** - отправить в Ollama для анализа
   - URL: `http://ollama:11434/api/generate`
   - Body: 
   ```json
   {
     "model": "llama2",
     "prompt": "Summarize this transcript: {{ $json.subtitles }}"
   }
   ```

5. **Set** - сохранить результаты

---

## Пример 6: Мониторинг и уведомления

### Workflow:
1. **Schedule** - проверка каждые 10 минут
2. **HTTP Request** - проверить здоровье сервиса
   - URL: `http://ytdlp:8081/health`
   
3. **IF** - если сервис недоступен
   - **Отправить email** с уведомлением
   - **Telegram/Slack** оповещение

---

## Пример 7: Создание медиа-библиотеки

### Workflow:
1. **Webhook** - добавить видео в библиотеку
2. **HTTP Request** - получить полную информацию
3. **HTTP Request** - скачать видео и превью
4. **LaBSE Embeddings** - создать embeddings для поиска
   - URL: `http://labse:8080/embeddings`
   - Body: 
   ```json
   {
     "texts": ["{{ $json.title }} {{ $json.description }}"]
   }
   ```

5. **Elasticsearch** - индексировать с embeddings
6. **PostgreSQL** - сохранить метаданные

---

## Полезные функции для n8n Code Node

### Проверка валидности URL
```javascript
function isValidYouTubeUrl(url) {
  const regex = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+$/;
  return regex.test(url);
}

const url = $input.item.json.url;
return {
  json: {
    isValid: isValidYouTubeUrl(url),
    url: url
  }
};
```

### Форматирование длительности
```javascript
function formatDuration(seconds) {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  
  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  }
  return `${minutes}:${String(secs).padStart(2, '0')}`;
}

const duration = $input.item.json.duration;
return {
  json: {
    ...($input.item.json),
    formatted_duration: formatDuration(duration)
  }
};
```

### Извлечение ID видео из URL
```javascript
function extractVideoId(url) {
  const regex = /(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})/;
  const match = url.match(regex);
  return match ? match[1] : null;
}

const url = $input.item.json.url;
return {
  json: {
    videoId: extractVideoId(url),
    originalUrl: url
  }
};
```

---

## Tips & Best Practices

### 1. Обработка ошибок
Всегда добавляйте обработку ошибок после HTTP Request нод:
- Используйте **IF** ноду для проверки статуса
- Добавьте **Error Trigger** для критических сбоев

### 2. Rate Limiting
YouTube и другие платформы имеют ограничения:
- Добавляйте **Wait** ноды между запросами
- Используйте **Split In Batches** для больших объёмов

### 3. Кэширование
Сохраняйте метаданные в базе данных:
- Проверяйте, не скачивали ли видео ранее
- Используйте Elasticsearch для быстрого поиска

### 4. Мониторинг
Добавьте мониторинг в ваши workflow:
- Логируйте все операции
- Отслеживайте успешность скачиваний
- Настройте уведомления о проблемах

### 5. Очистка
Регулярно очищайте старые файлы:
```bash
# Очистка файлов старше 30 дней
docker exec ytdlp find /downloads -type f -mtime +30 -delete
```

---

## Дополнительные ресурсы

- **YT-DLP API документация**: `/docker/ytdlp/README.md`
- **n8n документация**: https://docs.n8n.io/
- **YT-DLP поддерживаемые сайты**: https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md

---

**Примечание**: Все примеры используют внутренние Docker имена сервисов (`ytdlp`, `elasticsearch`, `ollama`), которые доступны внутри Docker сети. При тестировании вне Docker используйте `localhost`.
