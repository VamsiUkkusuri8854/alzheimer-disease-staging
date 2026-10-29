# ============================================================
# ALZHEIMER MRI STAGING - FASTAPI APPLICATION
# ============================================================

import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.health import router as health_router
from backend.routes.prediction import router as prediction_router
from backend.routes.chat import router as chat_router
from backend.services.model_service import ModelService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler: Preload model on startup once into memory.
    """
    print("\n" + "=" * 65)
    print("STARTING ALZHEIMER MRI STAGING BACKEND API")
    print("=" * 65)
    
    # Initialize ModelService singleton once
    model_service = ModelService.get_instance()
    if model_service.is_loaded:
        print(f"--> Model status: READY ({model_service.num_classes} classes on {model_service.device})")
    else:
        print(f"--> Model status: NOT LOADED ({model_service.error_message})")
    
    print("=" * 65 + "\n")
    yield
    print("\n[Backend] Shutting down Alzheimer MRI Staging API...")


# Create FastAPI application
app = FastAPI(
    title="Alzheimer MRI Staging API",
    description=(
        "Uncertainty-Aware Patient-Level Alzheimer's Disease Staging "
        "Using Lightweight Deep Learning and Structural MRI (MobileNetV3-Large)"
    ),
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS to allow access from any laptop/device on the local network
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.responses import JSONResponse
from fastapi import Request

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": f"Server error: {str(exc)}"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

# Register route modules
app.include_router(health_router)
app.include_router(prediction_router)
app.include_router(chat_router)


@app.get("/")
async def root():
    return {
        "title": "Uncertainty-Aware Alzheimer's Disease MRI Staging API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "health_url": "/health",
        "predict_url": "/predict",
        "model_info_url": "/model-info",
        "disclaimer": (
            "Research prototype only. This prediction is not a medical diagnosis "
            "and must not be used for clinical decision-making."
        )
    }


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("backend.main:app", host=host, port=port, reload=True)
