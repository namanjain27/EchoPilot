from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .routes import chat, knowledge_base

# Create FastAPI application
app = FastAPI(
    title="EchoPilot API",
    description="Customer Success Copilot API - RAG with tool calling",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router)
app.include_router(knowledge_base.router)

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "EchoPilot API is running", "version": "1.0.0"}

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    from datetime import datetime
    import os
    from echo_ui import get_vector_store_status
    
    try:
        # Check vector store
        vector_status = get_vector_store_status()
        vector_healthy = vector_status["status"] in ["ready", "empty"]
        
        # Check API key
        api_key_present = bool(os.environ.get("GOOGLE_API_KEY"))
        
        # Overall health
        healthy = vector_healthy and api_key_present
        
        return {
            "status": "healthy" if healthy else "unhealthy",
            "timestamp": datetime.now(),
            "services": {
                "vector_store": vector_healthy,
                "api_key": api_key_present,
                "agent": healthy
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now(),
            "error": str(e),
            "services": {
                "vector_store": False,
                "api_key": False,
                "agent": False
            }
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)