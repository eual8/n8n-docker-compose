from flask import Flask, request, jsonify
from flask_cors import CORS
from faster_whisper import WhisperModel
import os
import tempfile
import logging
from pathlib import Path

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Директория для временных файлов
TEMP_DIR = '/tmp/whisper'
os.makedirs(TEMP_DIR, exist_ok=True)

# Глобальные переменные для хранения модели
current_model = None
current_model_name = None

# Поддерживаемые расширения файлов
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'm4a', 'ogg', 'flac', 'webm', 'mp4'}

def allowed_file(filename):
    """Проверка допустимости расширения файла"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_whisper_model(model_name='base'):
    """Получение или инициализация Whisper модели"""
    global current_model, current_model_name
    
    if current_model is None or current_model_name != model_name:
        try:
            logger.info(f"Загрузка Whisper модели: {model_name}")
            # device="cpu" для CPU, можно изменить на "cuda" для GPU
            # compute_type="int8" для оптимизации памяти
            current_model = WhisperModel(model_name, device="cpu", compute_type="int8")
            current_model_name = model_name
            logger.info(f"Модель {model_name} успешно загружена")
        except Exception as e:
            logger.error(f"Ошибка при загрузке модели: {str(e)}")
            raise
    
    return current_model

@app.route('/health', methods=['GET'])
def health():
    """Проверка здоровья сервиса"""
    return jsonify({
        'status': 'healthy',
        'service': 'faster-whisper',
        'model_loaded': current_model is not None,
        'current_model': current_model_name
    }), 200

@app.route('/transcribe', methods=['POST'])
def transcribe():
    """
    Транскрипция аудио файла
    
    Принимает:
    - file: MP3/WAV/M4A файл (multipart/form-data)
    - model: название модели (опционально, по умолчанию 'base')
      Доступные модели: tiny, base, small, medium, large
    - language: код языка (опционально, auto-detect если не указан)
    - task: transcribe или translate (опционально, по умолчанию transcribe)
    
    Возвращает:
    - text: транскрибированный текст
    - segments: список сегментов с временными метками
    - language: определенный язык
    """
    try:
        # Проверка наличия файла
        if 'file' not in request.files:
            return jsonify({'error': 'Файл не предоставлен'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'Файл не выбран'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'error': f'Неподдерживаемый формат файла',
                'allowed_formats': list(ALLOWED_EXTENSIONS)
            }), 400
        
        # Получение параметров
        model_name = request.form.get('model', 'base')
        language = request.form.get('language', None)  # None для автоопределения
        task = request.form.get('task', 'transcribe')  # transcribe или translate
        
        # Сохранение временного файла
        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=Path(file.filename).suffix,
            dir=TEMP_DIR
        )
        
        try:
            file.save(temp_file.name)
            temp_file.close()
            
            logger.info(f"Файл сохранен: {temp_file.name}")
            
            # Получение модели
            model = get_whisper_model(model_name)
            
            # Транскрипция
            logger.info(f"Начало транскрипции файла '{file.filename}' с моделью {model_name}, язык: {language or 'auto'}, задача: {task}")
            
            segments, info = model.transcribe(
                temp_file.name,
                language=language,
                task=task,
                beam_size=5,
                vad_filter=True,  # Voice Activity Detection для лучшего качества
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            
            # Сборка результата
            result_segments = []
            full_text = []
            
            for segment in segments:
                result_segments.append({
                    'start': round(segment.start, 2),
                    'end': round(segment.end, 2),
                    'text': segment.text.strip()
                })
                full_text.append(segment.text.strip())
            
            response = {
                'text': ' '.join(full_text),
                'language': info.language,
                'language_probability': round(info.language_probability, 2),
                'duration': round(info.duration, 2),
                'segments': result_segments,
                'model': model_name
            }
            
            logger.info(f"Транскрипция завершена успешно. Язык: {info.language}, Длительность: {info.duration:.2f}s")
            
            return jsonify(response), 200
            
        finally:
            # Удаление временного файла
            try:
                os.unlink(temp_file.name)
                logger.info(f"Временный файл удален: {temp_file.name}")
            except Exception as e:
                logger.warning(f"Не удалось удалить временный файл: {str(e)}")
    
    except Exception as e:
        logger.error(f"Ошибка при транскрипции: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/models', methods=['GET'])
def list_models():
    """Список доступных моделей Whisper"""
    return jsonify({
        'models': [
            {
                'name': 'tiny',
                'size': '~75 MB',
                'description': 'Самая быстрая, наименее точная'
            },
            {
                'name': 'base',
                'size': '~142 MB',
                'description': 'Базовая модель (по умолчанию)'
            },
            {
                'name': 'small',
                'size': '~466 MB',
                'description': 'Небольшая модель, хорошая точность'
            },
            {
                'name': 'medium',
                'size': '~1.5 GB',
                'description': 'Средняя модель, высокая точность'
            },
            {
                'name': 'large',
                'size': '~2.9 GB',
                'description': 'Самая большая и точная модель'
            }
        ]
    }), 200

@app.route('/info', methods=['GET'])
def info():
    """Информация о сервисе"""
    return jsonify({
        'service': 'Whisper Audio Transcription Service (faster-whisper)',
        'version': '1.0.0',
        'description': 'API для транскрипции аудио файлов с использованием faster-whisper',
        'supported_formats': list(ALLOWED_EXTENSIONS),
        'endpoints': {
            '/health': 'GET - Проверка статуса сервиса',
            '/transcribe': 'POST - Транскрипция аудио файла',
            '/models': 'GET - Список доступных моделей',
            '/info': 'GET - Информация о сервисе'
        }
    }), 200

if __name__ == '__main__':
    logger.info("Запуск Whisper Transcription Service на порту 8082")
    app.run(host='0.0.0.0', port=8082, debug=False)
