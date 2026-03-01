from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

class StockRequest(BaseModel):
    symbol: str
    period: Optional[str] = "1y"

class PredictionRequest(BaseModel):
    symbol: str
    days: Optional[int] = 30

class StockData(BaseModel):
    symbol: str
    current_price: float
    price_change: float
    price_change_percent: float
    volume: int
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None

class CompanyInfo(BaseModel):
    symbol: str
    name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    website: Optional[str] = None
    employees: Optional[int] = None
    description: Optional[str] = None

class HistoricalData(BaseModel):
    dates: List[str]
    open: List[float]
    high: List[float]
    low: List[float]
    close: List[float]
    volume: List[int]

class TechnicalIndicators(BaseModel):
    rsi: float
    ma20: float
    ma50: float
    signal: str

class PredictionData(BaseModel):
    symbol: str
    forecast_days: int
    current_price: float
    predicted_price: float
    confidence_lower: float
    confidence_upper: float
    price_change: float
    price_change_percent: float
    predictions: List[Dict[str, Any]]
    day_1: float
    week_1: float  
    month_1: float
    confidence: Optional[Dict[str, float]] = None

class FinancialMetrics(BaseModel):
    market_cap: Optional[float] = None
    enterprise_value: Optional[float] = None
    pe_ratio: Optional[float] = None
    forward_pe: Optional[float] = None
    price_to_book: Optional[float] = None
    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    profit_margin: Optional[float] = None
    roe: Optional[float] = None
    roa: Optional[float] = None
    total_cash: Optional[float] = None
    total_debt: Optional[float] = None
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None