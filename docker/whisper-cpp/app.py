from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import tempfile
import logging
import subprocess
import json
from pathlib import Path

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Директория для временных файлов
TEMP_DIR = '/tmp/whisper'
os.makedirs(TEMP_DIR, exist_ok=True)

# Директория с моделями
MODELS_DIR = '/models'
os.makedirs(MODELS_DIR, exist_ok=True)

# Путь к бинарнику whisper.cpp
WHISPER_CPP_BIN = '/whisper.cpp/build/bin/whisper-cli'

# Маппинг названий моделей на файлы и параметры для скрипта скачивания
MODEL_FILES = {
    'tiny': {'file': 'ggml-tiny.bin', 'download_name': 'tiny'},
    'base': {'file': 'ggml-base.bin', 'download_name': 'base'},
    'small': {'file': 'ggml-small.bin', 'download_name': 'small'},
    'medium': {'file': 'ggml-medium.bin', 'download_name': 'medium'},
    'large': {'file': 'ggml-large-v3.bin', 'download_name': 'large-v3'},
    'large-v3': {'file': 'ggml-large-v3.bin', 'download_name': 'large-v3'}
}

# Поддерживаемые расширения файлов
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'm4a', 'ogg', 'flac', 'webm', 'mp4'}

def allowed_file(filename):
    """Проверка допустимости расширения файла"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def download_model(model_name):
    """Скачивание модели если она еще не скачана"""
    model_info = MODEL_FILES.get(model_name)
    if not model_info:
        raise ValueError(f"Неизвестная модель: {model_name}")
    
    model_file = model_info['file']
    download_name = model_info['download_name']
    
    model_path = os.path.join(MODELS_DIR, model_file)
    
    # Проверяем наличие модели в целевой директории
    if os.path.exists(model_path):
        file_size = os.path.getsize(model_path)
        # Проверяем, что файл не пустой (больше 1MB)
        if file_size > 1024 * 1024:
            logger.info(f"Модель {model_name} уже существует: {model_path} ({file_size / (1024**2):.1f} MB)")
            return model_path
        else:
            logger.warning(f"Найден битый файл модели (размер: {file_size} байт), удаляем...")
            os.unlink(model_path)
    
    # Проверяем, может модель уже есть в whisper.cpp/models
    whisper_models_dir = '/whisper.cpp/models'
    alt_path = os.path.join(whisper_models_dir, model_file)
    
    if os.path.exists(alt_path):
        file_size = os.path.getsize(alt_path)
        if file_size > 1024 * 1024:
            logger.info(f"Модель найдена в {alt_path} ({file_size / (1024**2):.1f} MB), копируем в {model_path}")
            subprocess.run(['cp', alt_path, model_path], check=True)
            logger.info(f"Модель {model_name} успешно скопирована: {model_path}")
            return model_path
        else:
            logger.warning(f"Найден битый файл модели в {alt_path} (размер: {file_size} байт), удаляем...")
            os.unlink(alt_path)
    
    logger.info(f"Скачивание модели {model_name} ({download_name})...")
    
    # Скрипт скачивания находится в /whisper.cpp/models/
    # По умолчанию он сохраняет модель в свою директорию (/whisper.cpp/models/)
    download_script = f"bash /whisper.cpp/models/download-ggml-model.sh {download_name}"
    
    try:
        # Запускаем скрипт из директории /whisper.cpp/models
        result = subprocess.run(
            download_script,
            shell=True,
            cwd=whisper_models_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"Ошибка скачивания модели: {result.stderr}")
            logger.error(f"Вывод скрипта: {result.stdout}")
            raise Exception(f"Не удалось скачать модель: {result.stderr}")
        
        logger.info(f"Скрипт выполнен успешно")
        
        # После скачивания файл должен быть в /whisper.cpp/models/
        if os.path.exists(alt_path):
            file_size = os.path.getsize(alt_path)
            if file_size > 1024 * 1024:
                logger.info(f"Модель скачана в {alt_path} ({file_size / (1024**2):.1f} MB), копируем в {model_path}")
                subprocess.run(['cp', alt_path, model_path], check=True)
            else:
                raise Exception(f"Скачанный файл модели слишком мал: {file_size} байт")
        else:
            raise Exception(f"Модель не найдена после скачивания: {alt_path}")
        
        # Финальная проверка
        if not os.path.exists(model_path):
            raise Exception(f"Модель не найдена в {model_path} после всех операций")
        
        logger.info(f"Модель {model_name} успешно установлена: {model_path}")
        return model_path
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Ошибка выполнения команды скачивания: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Ошибка при скачивании модели: {str(e)}")
        raise

def convert_to_wav(input_file):
    """Конвертация аудио файла в WAV формат для whisper.cpp"""
    output_file = input_file.rsplit('.', 1)[0] + '_16k.wav'
    
    # whisper.cpp требует 16kHz WAV файлы
    cmd = [
        'ffmpeg',
        '-i', input_file,
        '-ar', '16000',
        '-ac', '1',
        '-c:a', 'pcm_s16le',
        output_file,
        '-y'
    ]
    
    try:
        logger.info(f"Конвертация файла в WAV 16kHz: {input_file} -> {output_file}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Ошибка конвертации: {result.stderr}")
        logger.info(f"Конвертация завершена: {output_file}")
        return output_file
    except Exception as e:
        logger.error(f"Ошибка при конвертации файла: {str(e)}")
        raise

def run_whisper_cpp(audio_file, model_name='base', language=None, task='transcribe'):
    """Запуск whisper.cpp для транскрипции"""
    model_path = download_model(model_name)
    
    # Конвертация в нужный формат
    wav_file = convert_to_wav(audio_file)
    
    try:
        # Формирование команды
        cmd = [
            WHISPER_CPP_BIN,
            '-m', model_path,
            '-f', wav_file,
            '-oj',  # Вывод в JSON
            '-otxt',  # Вывод в текст
            '-t', '8',  # Количество потоков (можно увеличить)
            '-p', '1',  # Количество процессоров
        ]
        
        # Добавление языка если указан
        if language:
            cmd.extend(['-l', language])
        
        # Добавление задачи (translate)
        if task == 'translate':
            cmd.append('-tr')
        
        # Запуск whisper.cpp с потоковым выводом
        logger.info(f"Запуск whisper.cpp: {' '.join(cmd)}")
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,  # Построчная буферизация
            cwd=TEMP_DIR
        )
        
        # Чтение вывода в реальном времени
        for line in process.stdout:
            line = line.strip()
            if line:
                logger.info(f"whisper.cpp: {line}")
        
        # Ожидание завершения процесса
        return_code = process.wait()
        
        if return_code != 0:
            raise Exception(f"Ошибка whisper.cpp: процесс завершился с кодом {return_code}")
        
        # Чтение результатов
        json_file = wav_file.rsplit('.', 1)[0] + '.json'
        txt_file = wav_file.rsplit('.', 1)[0] + '.txt'
        
        segments = []
        full_text = ""
        detected_language = language or "unknown"
        
        # Парсинг JSON с сегментами
        if os.path.exists(json_file):
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'transcription' in data:
                    for segment in data['transcription']:
                        segments.append({
                            'start': round(segment['timestamps']['from'] / 1000.0, 2),
                            'end': round(segment['timestamps']['to'] / 1000.0, 2),
                            'text': segment['text'].strip()
                        })
        
        # Чтение полного текста
        if os.path.exists(txt_file):
            with open(txt_file, 'r', encoding='utf-8') as f:
                full_text = f.read().strip()
        else:
            full_text = ' '.join([s['text'] for s in segments])
        
        # Удаление временных файлов
        for temp_file in [json_file, txt_file, wav_file]:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
        
        return {
            'text': full_text,
            'segments': segments,
            'language': detected_language
        }
        
    except Exception as e:
        # Очистка временных файлов при ошибке
        if os.path.exists(wav_file):
            os.unlink(wav_file)
        raise

@app.route('/health', methods=['GET'])
def health():
    """Проверка здоровья сервиса"""
    return jsonify({
        'status': 'healthy',
        'service': 'whisper-cpp',
        'whisper_cpp_available': os.path.exists(WHISPER_CPP_BIN)
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
        
        # Валидация модели
        if model_name not in MODEL_FILES:
            return jsonify({
                'error': f'Неизвестная модель: {model_name}',
                'available_models': list(MODEL_FILES.keys())
            }), 400
        
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
            logger.info(f"Начало транскрипции файла '{file.filename}' с моделью {model_name}, язык: {language or 'auto'}, задача: {task}")
            
            # Транскрипция через whisper.cpp
            result = run_whisper_cpp(temp_file.name, model_name, language, task)
            
            response = {
                'text': result['text'],
                'language': result['language'],
                'language_probability': 0.99,  # whisper.cpp не предоставляет эту метрику
                'duration': 0.0,  # можно добавить расчет длительности если нужно
                'segments': result['segments'],
                'model': model_name
            }
            
            logger.info(f"Транскрипция завершена успешно. Язык: {result['language']}")
            
            return jsonify(response), 200
            
        finally:
            # Удаление временного файла
            try:
                if os.path.exists(temp_file.name):
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
                'description': 'Самая большая и точная модель (large-v3)'
            },
            {
                'name': 'large-v3',
                'size': '~2.9 GB',
                'description': 'Самая большая и точная модель'
            }
        ]
    }), 200

@app.route('/info', methods=['GET'])
def info():
    """Информация о сервисе"""
    return jsonify({
        'service': 'Whisper Audio Transcription Service (whisper.cpp)',
        'version': '1.0.0',
        'description': 'API для транскрипции аудио файлов с использованием whisper.cpp',
        'supported_formats': list(ALLOWED_EXTENSIONS),
        'endpoints': {
            '/health': 'GET - Проверка статуса сервиса',
            '/transcribe': 'POST - Транскрипция аудио файла',
            '/models': 'GET - Список доступных моделей',
            '/info': 'GET - Информация о сервисе'
        }
    }), 200

if __name__ == '__main__':
    logger.info("Запуск Whisper.cpp Transcription Service на порту 8083")
    app.run(host='0.0.0.0', port=8083, debug=False)
