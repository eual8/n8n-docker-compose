FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Установка yt-dlp и Flask
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    yt-dlp \
    flask \
    flask-cors

# Создание директории для загрузок
RUN mkdir -p /downloads

# Копирование приложения
COPY app.py /app/app.py

WORKDIR /app

# Открытие порта
EXPOSE 8081

# Запуск приложения
CMD ["python", "app.py"]
