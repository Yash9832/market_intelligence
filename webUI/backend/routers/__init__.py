from .stocks import router as stocks_router
from .predictions import router as predictions_router
from .market import router as market_router

__all__ = [
    "stocks_router",
    "predictions_router", 
    "market_router"
]