# Настройка n8n с OpenAI API

## Шаги для запуска

### 1. Настройка переменных окружения

Создайте файл `.env` в корне проекта на основе `.env.example`:

```bash
cp .env.example .env
```

Откройте `.env` и добавьте ваш OpenAI API ключ:

```bash
OPENAI_API_KEY=sk-ваш-реальный-ключ-здесь
```

**Где взять API ключ:**
- Перейдите на https://platform.openai.com/api-keys
- Войдите в свой аккаунт OpenAI
- Создайте новый API ключ
- Скопируйте и вставьте его в `.env` файл

### 2. Перезапуск контейнеров

После добавления API ключа, перезапустите контейнеры:

```bash
docker-compose down
docker-compose up -d
```

### 3. Проверка

Откройте n8n в браузере:
```
http://localhost:5678
```

Теперь воркфлоу "STT stream OpenAI" (ID: 1CHfBBKGhaahDgVX) должен работать корректно.

## Что было исправлено

**Проблема:** В Code node использовался метод `this.getCredentials()`, который не доступен в обычных Code nodes.

**Решение:** 
1. Добавлена переменная окружения `OPENAI_API_KEY` в `docker-compose.yml`
2. Обновлён код в воркфлоу для использования `process.env.OPENAI_API_KEY`
3. Также изменена модель с `gpt-4o-mini-transcribe` на `whisper-1` (стандартная модель для транскрибации)

## Безопасность

⚠️ **Важно:** Не коммитьте файл `.env` в git! Он уже добавлен в `.gitignore`.

Для продакшена рекомендуется использовать secrets management системы (Docker Secrets, Kubernetes Secrets, AWS Secrets Manager и т.д.)
