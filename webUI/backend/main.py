from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

# Import routers - use absolute imports within the webUI.backend package
from webUI.backend.routers.stocks import router as stocks_router
from webUI.backend.routers.predictions import router as predictions_router  
from webUI.backend.routers.market import router as market_router
from webUI.backend.routers.chatbot import router as chatbot_router
from webUI.backend.models.schemas import APIResponse
from webUI.backend.services.rss_service import rss_monitor

# Configure enhanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)

# Also configure chatbot service logger to be more verbose
chatbot_logger = logging.getLogger('services.chatbot_service')
chatbot_logger.setLevel(logging.INFO)

# Create FastAPI app
app = FastAPI(
    title="Financial Dashboard API",
    description="REST API for stock data, financial analysis, and price predictions",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(stocks_router)
app.include_router(predictions_router)
app.include_router(market_router)
app.include_router(chatbot_router)

@app.get("/", response_model=APIResponse)
async def root():
    """API health check endpoint"""
    return APIResponse(
        success=True,
        message="Financial Dashboard API is running successfully",
        data={
            "version": "1.0.0",
            "status": "healthy",
            "docs": "/docs",
            "endpoints": {
                "stocks": "/stocks",
                "predictions": "/predictions", 
                "market": "/market"
            }
        }
    )

@app.get("/health", response_model=APIResponse)
async def health_check():
    """Detailed health check endpoint"""
    return APIResponse(
        success=True,
        message="API is healthy",
        data={
            "status": "healthy",
            "timestamp": "2025-09-20T00:00:00Z"
        }
    )

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content=APIResponse(
            success=False,
            message="An unexpected error occurred",
            data=None
        ).dict()
    )


@app.on_event("startup")
async def startup_event():
    # Start RSS monitor background task (check every 3 minutes)
    import asyncio
    asyncio.create_task(rss_monitor.run_monitor(check_interval=180))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)