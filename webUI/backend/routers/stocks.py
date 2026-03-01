from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from typing import Optional, List
import json
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.schemas import APIResponse, StockRequest
from services.stock_service import StockService
from services.rss_service import rss_monitor

router = APIRouter(prefix="/stocks", tags=["stocks"])

@router.get("/search", response_model=APIResponse)
async def search_stocks(
    query: str = Query(..., description="Search query for stocks"),
    limit: int = Query(10, description="Maximum number of results")
):
    """Search for stocks by symbol or company name"""
    try:
        results = StockService.search_stocks(query, limit)
        return APIResponse(
            success=True,
            message="Stock search completed successfully",
            data={"results": results}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/news/ws/{session_id}")
async def news_websocket(websocket: WebSocket, session_id: str):
    await rss_monitor.websocket_manager.connect(websocket, session_id)
    try:
        while True:
            message = await websocket.receive_text()
            try:
                data = json.loads(message)
            except Exception:
                continue
            if data.get("type") == "set_keywords":
                keywords = data.get("keywords", [])
                rss_monitor.websocket_manager.update_user_keywords(session_id, keywords)
                await rss_monitor.websocket_manager.send_to_user(session_id, {
                    "type": "keywords_updated",
                    "keywords": keywords
                })
                rss_monitor._load_seen_articles(session_id)
                # Immediately process feeds so user sees results without waiting for the interval
                try:
                    await rss_monitor.process_feeds_for_user(session_id)
                    # Also send recent articles as a backfill
                    recent = rss_monitor.db.get_recent_articles(hours=48, limit=20, user_session=session_id)
                    for article_data in recent:
                        await rss_monitor.websocket_manager.send_to_user(session_id, {
                            "type": "recent_article",
                            "article": {
                                "id": article_data[0],
                                "title": article_data[1],
                                "description": article_data[2],
                                "link": article_data[3],
                                "source": article_data[4],
                                "published": article_data[5],
                                "matched_keywords": article_data[6].split(',') if article_data[6] else [],
                                "timestamp": article_data[7]
                            }
                        })
                except Exception:
                    pass
            elif data.get("type") == "get_recent":
                recent = rss_monitor.db.get_recent_articles(hours=6, limit=20, user_session=session_id)
                for article_data in recent:
                    await rss_monitor.websocket_manager.send_to_user(session_id, {
                        "type": "recent_article",
                        "article": {
                            "id": article_data[0],
                            "title": article_data[1],
                            "description": article_data[2],
                            "link": article_data[3],
                            "source": article_data[4],
                            "published": article_data[5],
                            "matched_keywords": article_data[6].split(',') if article_data[6] else [],
                            "timestamp": article_data[7]
                        }
                    })
    except WebSocketDisconnect:
        rss_monitor.websocket_manager.disconnect(session_id)

@router.get("/{symbol}/info", response_model=APIResponse)
async def get_stock_info(symbol: str):
    """Get basic stock information and company details"""
    try:
        stock_data, company_info = StockService.get_stock_info(symbol.upper())
        
        if not stock_data:
            raise HTTPException(status_code=404, detail=f"Stock data not found for symbol: {symbol}")
        
        return APIResponse(
            success=True,
            message="Stock information retrieved successfully",
            data={
                "stock_data": stock_data.dict(),
                "company_info": company_info.dict() if company_info else None
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{symbol}/historical", response_model=APIResponse)
async def get_historical_data(
    symbol: str,
    period: str = Query("1y", description="Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)")
):
    """Get historical stock data"""
    try:
        historical_data = StockService.get_historical_data(symbol.upper(), period)
        
        if not historical_data:
            raise HTTPException(status_code=404, detail=f"Historical data not found for symbol: {symbol}")
        
        return APIResponse(
            success=True,
            message="Historical data retrieved successfully",
            data=historical_data.dict()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{symbol}/financials", response_model=APIResponse)
async def get_financial_metrics(symbol: str):
    """Get detailed financial metrics for a stock"""
    try:
        financial_metrics = StockService.get_financial_metrics(symbol.upper())
        
        if not financial_metrics:
            raise HTTPException(status_code=404, detail=f"Financial data not found for symbol: {symbol}")
        
        return APIResponse(
            success=True,
            message="Financial metrics retrieved successfully",
            data=financial_metrics.dict()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))