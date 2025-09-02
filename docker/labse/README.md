# LaBSE Embeddings Service

A FastAPI service for the LaBSE (Language-agnostic BERT Sentence Embedding) model that provides multilingual text embeddings via HTTP API.

## Features

- 🌍 Supports 109 languages
- 📊 768-dimensional embeddings
- 🚀 FastAPI with automatic API documentation
- 🐳 Docker containerized
- ⚡ Batch processing support

## API Endpoints

### Health Check
```
GET /health
```

### Generate Embeddings
```
POST /embeddings
```

Request body:
```json
{
  "texts": ["Hello world", "Привет мир", "Hola mundo"],
  "normalize": true
}
```

Response:
```json
{
  "embeddings": [[...], [...], [...]],
  "dimensions": 768,
  "count": 3
}
```

### Calculate Similarity
```
POST /similarity
```

Request body:
```json
{
  "text1": "Hello world",
  "text2": "Привет мир"
}
```

Response:
```json
{
  "text1": "Hello world",
  "text2": "Привет мир",
  "similarity": 0.892
}
```

## Usage Examples

### Python
```python
import requests

# Generate embeddings
response = requests.post('http://localhost:8080/embeddings', 
    json={"texts": ["Hello world", "Test text"]})
embeddings = response.json()['embeddings']

# Calculate similarity
response = requests.post('http://localhost:8080/similarity',
    json={"text1": "Hello", "text2": "Hi"})
similarity = response.json()['similarity']
```

### cURL
```bash
# Generate embeddings
curl -X POST http://localhost:8080/embeddings \
  -H "Content-Type: application/json" \
  -d '{"texts": ["Hello world"]}'

# Calculate similarity
curl -X POST http://localhost:8080/similarity \
  -H "Content-Type: application/json" \
  -d '{"text1": "Hello", "text2": "Hi"}'
```

## API Documentation

Interactive API documentation is available at:
- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

## Building and Running

The service is integrated with docker-compose. To build and run:

```bash
# Build and start all services
docker-compose up -d --build

# View logs
docker-compose logs -f labse

# Stop the service
docker-compose down
```

## Performance Notes

- First request will be slower as the model loads into memory (~1.8GB)
- Subsequent requests will be fast
- The model is cached in the `labse_cache` volume to speed up container restarts

## Model Information

- Model: [sentence-transformers/LaBSE](https://huggingface.co/sentence-transformers/LaBSE)
- Architecture: BERT-based
- Languages: 109 languages supported
- Embedding dimensions: 768
- Use case: Multilingual semantic similarity and search
