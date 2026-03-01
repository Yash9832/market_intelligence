from fastapi import APIRouter, HTTPException, Query
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.schemas import APIResponse
from services.market_service import MarketService

router = APIRouter(prefix="/market", tags=["market"])

@router.get("/indices", response_model=APIResponse)
async def get_market_indices():
    """Get major market indices data"""
    try:
        indices_data = MarketService.get_market_indices()
        
        return APIResponse(
            success=True,
            message="Market indices data retrieved successfully",
            data={"indices": indices_data}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/movers", response_model=APIResponse)
async def get_market_movers(
    category: str = Query("gainers", description="Category: 'gainers' or 'losers'"),
    market: str = Query("US", description="Market: 'US' or 'India'"),
    limit: int = Query(10, description="Number of results", ge=1, le=50)
):
    """Get market movers (top gainers or losers)"""
    try:
        if category not in ["gainers", "losers"]:
            raise HTTPException(status_code=400, detail="Category must be 'gainers' or 'losers'")
        
        if market not in ["US", "India"]:
            raise HTTPException(status_code=400, detail="Market must be 'US' or 'India'")
        
        movers_data = MarketService.get_market_movers(category, market, limit)
        
        return APIResponse(
            success=True,
            message=f"Market {category} retrieved successfully",
            data={
                "category": category,
                "market": market,
                "movers": movers_data
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))