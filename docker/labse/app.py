from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer
from typing import List, Union, Optional
import numpy as np
import logging
import os
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variable to store the model
model = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model on startup and clean up on shutdown"""
    global model
    try:
        logger.info("Loading LaBSE model...")
        model = SentenceTransformer('sentence-transformers/LaBSE')
        logger.info("LaBSE model loaded successfully!")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise
    yield
    # Cleanup
    logger.info("Shutting down...")

# Create FastAPI app
app = FastAPI(
    title="LaBSE Embeddings API",
    description="API for generating multilingual text embeddings using LaBSE model",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class EmbeddingRequest(BaseModel):
    texts: Union[str, List[str]] = Field(
        ...,
        description="Single text or list of texts to generate embeddings for",
        example=["Hello world", "Привет мир", "Hola mundo"]
    )
    normalize: Optional[bool] = Field(
        default=True,
        description="Whether to normalize embeddings to unit length"
    )

class EmbeddingResponse(BaseModel):
    embeddings: List[List[float]] = Field(
        ...,
        description="List of embedding vectors"
    )
    dimensions: int = Field(
        ...,
        description="Dimension of each embedding vector"
    )
    count: int = Field(
        ...,
        description="Number of embeddings generated"
    )

class HealthResponse(BaseModel):
    status: str
    model: str
    dimensions: int

# Endpoints
@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - returns API status"""
    return {
        "status": "online",
        "model": "sentence-transformers/LaBSE",
        "dimensions": 768
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return {
        "status": "healthy",
        "model": "sentence-transformers/LaBSE",
        "dimensions": 768
    }

@app.post("/embeddings", response_model=EmbeddingResponse)
async def get_embeddings(request: EmbeddingRequest):
    """
    Generate embeddings for text(s) using LaBSE model.
    
    Supports 109 languages and returns 768-dimensional vectors.
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Convert single text to list
        if isinstance(request.texts, str):
            texts = [request.texts]
        else:
            texts = request.texts
        
        # Validate input
        if len(texts) == 0:
            raise HTTPException(status_code=400, detail="No texts provided")
        
        if len(texts) > 100:
            raise HTTPException(status_code=400, detail="Maximum 100 texts allowed per request")
        
        # Generate embeddings
        logger.info(f"Generating embeddings for {len(texts)} text(s)")
        embeddings = model.encode(texts, normalize_embeddings=request.normalize)
        
        # Convert to list format
        embeddings_list = embeddings.tolist()
        
        return {
            "embeddings": embeddings_list,
            "dimensions": embeddings.shape[1],
            "count": len(embeddings_list)
        }
    
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
