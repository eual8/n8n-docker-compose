FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    cmake \
    ffmpeg \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Клонирование и сборка whisper.cpp
WORKDIR /
RUN git clone https://github.com/ggerganov/whisper.cpp.git && \
    cd whisper.cpp && \
    make

# Создание директории для моделей
RUN mkdir -p /models

# Создание рабочей директории для приложения
WORKDIR /app

# Копирование файлов зависимостей
COPY requirements.txt .

# Обновление pip и установка зависимостей Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копирование приложения
COPY app.py .

# Создание директории для временных файлов
RUN mkdir -p /tmp/whisper

# Открытие порта
EXPOSE 8083

# Запуск приложения
CMD ["python", "app.py"]
