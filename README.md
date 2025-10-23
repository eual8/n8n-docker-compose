# n8n Docker Compose Stack

A complete Docker Compose setup for running n8n automation workflows with integrated AI services and document processing capabilities.

## 🚀 What is this repository?

This repository provides a ready-to-use Docker Compose stack that includes:

- **n8n** - No-code automation platform for building workflows
- **Elasticsearch** - Search and analytics engine for document indexing
- **Ollama** - Local LLM inference server for AI capabilities
- **LaBSE** - Multilingual text embeddings service (109 languages supported)
- **YT-DLP** - YouTube and video platform downloader with REST API
- **Whisper** - Audio transcription service using OpenAI Whisper (faster-whisper)

## 🎯 Why use this stack?

This setup is perfect for:

- **Document Processing & Search**: Upload text files, automatically split them into paragraphs, and index them in Elasticsearch for semantic search
- **AI-Powered Workflows**: Leverage local LLM models through Ollama for text processing, analysis, and generation
- **Multilingual Text Analysis**: Use LaBSE embeddings for cross-language semantic similarity and search
- **Audio Transcription**: Convert audio files to text using state-of-the-art Whisper models
- **No-Code Automation**: Build complex workflows without programming using n8n's visual interface
- **Privacy-First AI**: All AI processing happens locally - no data sent to external APIs

## 📋 Services Overview

| Service | Port | Purpose | Access |
|---------|------|---------|--------|
| **n8n** | 5678 | Workflow automation platform | http://localhost:5678 |
| **Elasticsearch** | 9200 | Document search and analytics | http://localhost:9200 |
| **Ollama** | 11434 | Local LLM inference server | http://localhost:11434 |
| **LaBSE** | 8080 | Multilingual embeddings API | http://localhost:8080 |
| **YT-DLP** | 8081 | YouTube video/audio downloader | http://localhost:8081 |
| **Whisper** | 8082 | Audio transcription service | http://localhost:8082 |

## 🎬 Ready-to-Use Workflows

### YouTube Video Transcription (Manual)

Automatically transcribe YouTube videos to text:

1. **Open n8n**: http://localhost:5678 (login: admin / password)
2. **Find workflow**: "YouTube Video Transcription (Manual)"
3. **Edit URL**: Open "Enter YouTube URL" node and paste your YouTube link
4. **Run**: Click "Execute workflow"
5. **Get result**: View transcription in "Format Response" node

📖 **Full instructions**: See `workflows/QUICK_START.md`

**Features:**
- ✅ Simple form-based input
- ✅ Automatic audio extraction
- ✅ Multi-language support (auto-detect or specify)
- ✅ Timestamped segments
- ✅ Multiple Whisper models (tiny to large)

## 🛠 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- At least 4GB RAM available (for AI models)
- 10GB free disk space

### 1. Clone and Start

```bash
git clone <repository-url>
cd n8n-docker-compose
docker-compose up -d --build
```

### 2. Access n8n

- Open http://localhost:5678
- Login with:
  - Username: `admin`
  - Password: `password`

### 3. Import Sample Workflow

1. In n8n, go to **Workflows** → **Import from File**
2. Upload `workflows/Text File to Elasticsearch Indexer - Working Version.json`
3. Activate the workflow

## 📊 Sample Workflow: Text File Indexer

The included workflow demonstrates the stack's capabilities:

1. **File Upload**: Web form for uploading text files
2. **Text Processing**: Automatically splits content into paragraphs
3. **Elasticsearch Indexing**: Stores processed documents with metadata
4. **Batch Processing**: Handles large files efficiently

### How to use:
1. Activate the "Text File to Elasticsearch Indexer" workflow
2. Open the webhook URL provided by the form trigger
3. Upload a `.txt` file
4. Documents will be automatically indexed in Elasticsearch

## 🔧 Service Details

### n8n Configuration
- Basic authentication enabled
- Persistent data storage
- Connected to all other services
- Production-ready settings

### Elasticsearch
- Single-node setup
- No security (for local development)
- Persistent data volume
- Optimized for document storage

### Ollama
- Ready for LLM model installation
- Persistent model storage
- GPU acceleration support (if available)

### LaBSE Embeddings
- FastAPI-based service
- Supports 109 languages
- 768-dimensional embeddings
- Batch processing capable

### YT-DLP Service
- Download videos from YouTube and 1000+ sites
- Extract audio in MP3 format
- Get video metadata and transcripts
- REST API for easy integration

### Whisper Transcription
- Audio-to-text transcription using faster-whisper
- Support for multiple audio formats (MP3, WAV, M4A, OGG, FLAC, WebM)
- Automatic language detection
- Multiple model sizes (tiny, base, small, medium, large)
- Timestamp generation for each segment
- Optional translation to English

## 📚 Usage Examples

### Generate Embeddings
```bash
curl -X POST http://localhost:8080/embeddings \
  -H "Content-Type: application/json" \
  -d '{"texts": ["Hello world", "Привет мир", "Hola mundo"]}'
```

### Search Elasticsearch
```bash
curl -X GET "http://localhost:9200/documents/_search?q=your_search_term"
```

### Install Ollama Models
```bash
docker exec -it ollama ollama pull llama2
```

### Download YouTube Video
```bash
curl -X POST http://localhost:8081/download \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=VIDEO_ID", "format": "video", "quality": "best"}'
```

### Download YouTube Audio (MP3)
```bash
curl -X POST http://localhost:8081/download \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=VIDEO_ID", "format": "audio"}'
```

### Transcribe Audio File
```bash
# Basic transcription
curl -X POST http://localhost:8082/transcribe \
  -F "file=@audio.mp3"

# With specific model and language
curl -X POST http://localhost:8082/transcribe \
  -F "file=@audio.mp3" \
  -F "model=small" \
  -F "language=ru"

# Translate to English
curl -X POST http://localhost:8082/transcribe \
  -F "file=@audio.mp3" \
  -F "translate=true"
```

## 🔍 API Documentation

- **LaBSE API**: http://localhost:8080/docs
- **YT-DLP API**: See `docker/ytdlp/README.md` for full API documentation
- **Whisper API**: See `docker/whisper/README.md` for full API documentation
- **Elasticsearch**: http://localhost:9200
- **n8n Webhooks**: Available through workflow triggers

## 💾 Data Persistence

All data is persisted in Docker volumes:
- `n8n_data` - n8n workflows and settings
- `esdata` - Elasticsearch indices
- `ollama_data` - Downloaded LLM models  
- `labse_cache` - Cached embedding models
- `ytdlp_downloads` - Downloaded videos and audio files
- `ytdlp_cache` - yt-dlp cache
- `whisper_cache` - Whisper models cache

## 🚀 Advanced Usage

### Custom Workflows
Create workflows that combine:
- File processing with LaBSE embeddings
- AI text generation with Ollama
- Document search with Elasticsearch
- Web scraping and data transformation
- Download YouTube videos with YT-DLP and transcribe with Whisper
- Audio transcription and text analysis with Ollama

### Scaling
- Add more Elasticsearch nodes for clustering
- Use external GPU for Ollama acceleration
- Deploy behind reverse proxy for production

## 🛠 Troubleshooting

### Common Issues

**Services not starting?**
- Check Docker logs: `docker-compose logs [service-name]`
- Ensure ports are not in use
- Verify sufficient disk space and RAM

**n8n workflows failing?**
- Check service connectivity between containers
- Verify Elasticsearch is ready before running workflows
- Check webhook URLs and credentials

**LaBSE model loading slowly?**
- First request downloads ~1.8GB model
- Subsequent requests are fast
- Model is cached in volume

## 📝 Default Credentials

- **n8n**: admin / password
- **Elasticsearch**: No authentication
- **Other services**: No authentication (local development)

## 🤝 Contributing

Feel free to:
- Add new workflows to the `workflows/` directory
- Improve service configurations
- Add new AI services or tools
- Submit issues and pull requests

## 📄 License

This project is provided as-is for educational and development purposes.
