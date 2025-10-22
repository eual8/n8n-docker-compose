FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Создание рабочей директории
WORKDIR /app

# Копирование файлов зависимостей
COPY requirements.txt .

# Обновление pip и установка зависимостей
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копирование приложения
COPY app.py .

# Создание директории для временных файлов
RUN mkdir -p /tmp/whisper

# Открытие порта
EXPOSE 8082

# Запуск приложения
CMD ["python", "app.py"]
