from fastapi import APIRouter, HTTPException, Query
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.schemas import APIResponse, PredictionRequest
from services.prediction_service import PredictionService

router = APIRouter(prefix="/predictions", tags=["predictions"])

@router.post("/{symbol}", response_model=APIResponse)
async def predict_stock_price(
    symbol: str,
    forecast_days: int = Query(30, description="Number of days to forecast", ge=1, le=90)
):
    """Predict stock prices using Prophet model"""
    try:
        prediction_data = PredictionService.predict_stock_price(symbol.upper(), forecast_days)
        
        if not prediction_data:
            raise HTTPException(
                status_code=404, 
                detail=f"Unable to generate predictions for symbol: {symbol}. Insufficient data or invalid symbol."
            )
        
        return APIResponse(
            success=True,
            message=f"Price prediction generated successfully for {symbol}",
            data=prediction_data.dict()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{symbol}/technical", response_model=APIResponse)
async def get_technical_analysis(
    symbol: str,
    period: str = Query("1y", description="Time period for analysis")
):
    """Get technical analysis indicators"""
    try:
        technical_data = PredictionService.calculate_technical_indicators(symbol.upper(), period)
        
        if not technical_data:
            raise HTTPException(status_code=404, detail=f"Technical data not found for symbol: {symbol}")
        
        return APIResponse(
            success=True,
            message="Technical analysis completed successfully",
            data=technical_data
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))