from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import os
import json

app = Flask(__name__)
CORS(app)

DOWNLOAD_DIR = '/downloads'

@app.route('/health', methods=['GET'])
def health():
    """Проверка здоровья сервиса"""
    return jsonify({'status': 'healthy', 'service': 'yt-dlp'}), 200

@app.route('/info', methods=['POST'])
def get_video_info():
    """Получение информации о видео без скачивания"""
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            # Добавляем параметры для обхода ограничений YouTube
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web']
                }
            },
            # Добавляем User-Agent
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Извлекаем основную информацию
            video_info = {
                'title': info.get('title'),
                'description': info.get('description'),
                'duration': info.get('duration'),
                'uploader': info.get('uploader'),
                'upload_date': info.get('upload_date'),
                'view_count': info.get('view_count'),
                'like_count': info.get('like_count'),
                'thumbnail': info.get('thumbnail'),
                'formats': [
                    {
                        'format_id': f.get('format_id'),
                        'ext': f.get('ext'),
                        'resolution': f.get('resolution'),
                        'filesize': f.get('filesize'),
                    }
                    for f in info.get('formats', [])
                ]
            }
            
        return jsonify(video_info), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download', methods=['POST'])
def download_video():
    """Скачивание видео или аудио"""
    try:
        data = request.get_json()
        url = data.get('url')
        format_type = data.get('format', 'video')  # 'video', 'audio', или 'best'
        quality = data.get('quality', 'best')  # 'best', '1080p', '720p', и т.д.
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Настройки для скачивания
        ydl_opts = {
            'outtmpl': os.path.join(DOWNLOAD_DIR, '%(id)s.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
            # Добавляем параметры для обхода ограничений YouTube
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web']
                    # Убираем 'skip' чтобы не блокировать доступные форматы
                }
            },
            # Добавляем User-Agent
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            },
            # Игнорируем ошибки для более стабильной работы
            'ignoreerrors': False,
            # Разрешаем использовать все доступные форматы
            'allow_unplayable_formats': False,
        }
        
        # Настройка формата в зависимости от типа
        if format_type == 'audio':
            ydl_opts.update({
                # Самый простой и надёжный вариант для аудио
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        elif format_type == 'video':
            # Используем самый простой и надёжный селектор
            # Это всегда сработает, так как YouTube всегда имеет хотя бы один формат
            ydl_opts['format'] = 'best'
            # Опционально добавляем merge если нужно объединить видео и аудио
            if quality != 'best':
                height = quality.replace("p", "")
                ydl_opts['format'] = f'best[height<={height}]/best'
        else:
            ydl_opts['format'] = 'best'
        
        # Скачивание
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Если это аудио, имя файла изменится после постобработки
            if format_type == 'audio':
                filename = os.path.splitext(filename)[0] + '.mp3'
            
        return jsonify({
            'status': 'success',
            'filename': os.path.basename(filename),
            'path': filename,
            'title': info.get('title'),
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download-transcript', methods=['POST'])
def download_transcript():
    """Получение субтитров/транскрипта видео"""
    try:
        data = request.get_json()
        url = data.get('url')
        lang = data.get('lang', 'en')  # Язык субтитров
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        ydl_opts = {
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': [lang],
            'subtitlesformat': 'json3',
            'quiet': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Получение субтитров
            subtitles = info.get('subtitles', {})
            automatic_captions = info.get('automatic_captions', {})
            
            available_subs = {}
            if lang in subtitles:
                available_subs['manual'] = subtitles[lang]
            if lang in automatic_captions:
                available_subs['automatic'] = automatic_captions[lang]
            
            if not available_subs:
                return jsonify({
                    'error': f'No subtitles available for language: {lang}',
                    'available_languages': list(subtitles.keys()) + list(automatic_captions.keys())
                }), 404
            
        return jsonify({
            'status': 'success',
            'subtitles': available_subs,
            'title': info.get('title'),
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Создание директории для загрузок, если её нет
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    # Запуск сервера
    app.run(host='0.0.0.0', port=8081, debug=False)
