from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import yfinance as yf
import pandas as pd
import numpy as np
from prophet import Prophet
from datetime import datetime, timedelta
import json

app = FastAPI(
    title="Financial Dashboard API",
    description="REST API for stock data, fundamentals, and price predictions",
    version="1.0.0"
)

# Enable CORS for Streamlit integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class StockRequest(BaseModel):
    symbol: str
    days: Optional[int] = 30

class PredictionRequest(BaseModel):
    symbol: str
    forecast_days: Optional[int] = 30

@app.get("/")
async def root():
    return {"message": "Financial Dashboard API", "status": "active"}

@app.get("/api/stock/{symbol}/info")
async def get_stock_info(symbol: str):
    """Get basic company information"""
    try:
        ticker = yf.Ticker(symbol.upper())
        info = ticker.info
        
        # Extract key metrics
        key_info = {
            "symbol": symbol.upper(),
            "shortName": info.get("shortName", "N/A"),
            "longName": info.get("longName", "N/A"),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "country": info.get("country", "N/A"),
            "website": info.get("website", "N/A"),
            "marketCap": info.get("marketCap", 0),
            "enterpriseValue": info.get("enterpriseValue", 0),
            "trailingPE": info.get("trailingPE", 0),
            "forwardPE": info.get("forwardPE", 0),
            "priceToBook": info.get("priceToBook", 0),
            "debtToEquity": info.get("debtToEquity", 0),
            "returnOnEquity": info.get("returnOnEquity", 0),
            "revenueGrowth": info.get("revenueGrowth", 0),
            "grossMargins": info.get("grossMargins", 0),
            "operatingMargins": info.get("operatingMargins", 0),
            "profitMargins": info.get("profitMargins", 0),
            "currentPrice": info.get("currentPrice", 0),
            "regularMarketOpen": info.get("regularMarketOpen", 0),
            "regularMarketHigh": info.get("regularMarketHigh", 0),
            "regularMarketLow": info.get("regularMarketLow", 0),
            "volume": info.get("volume", 0),
            "averageVolume": info.get("averageVolume", 0),
            "fiftyTwoWeekHigh": info.get("fiftyTwoWeekHigh", 0),
            "fiftyTwoWeekLow": info.get("fiftyTwoWeekLow", 0),
            "beta": info.get("beta", 0),
            "dividendYield": info.get("dividendYield", 0),
            "payoutRatio": info.get("payoutRatio", 0),
            "totalCash": info.get("totalCash", 0),
            "totalDebt": info.get("totalDebt", 0),
            "freeCashflow": info.get("freeCashflow", 0),
            "operatingCashflow": info.get("operatingCashflow", 0),
            "earningsGrowth": info.get("earningsGrowth", 0),
            "recommendationKey": info.get("recommendationKey", "N/A"),
            "numberOfAnalystOpinions": info.get("numberOfAnalystOpinions", 0)
        }
        
        return {"status": "success", "data": key_info}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error fetching stock info: {str(e)}")

@app.get("/api/stock/{symbol}/financials")
async def get_financials(symbol: str):
    """Get company financial statements"""
    try:
        ticker = yf.Ticker(symbol.upper())
        
        # Get financial statements
        income_statement = ticker.financials
        balance_sheet = ticker.balance_sheet
        cashflow = ticker.cashflow
        
        # Convert to dictionaries and handle NaN values
        def clean_financial_data(df):
            if df.empty:
                return {}
            # Convert to dict and replace NaN with None
            data = df.to_dict()
            for key, values in data.items():
                for subkey, value in values.items():
                    if pd.isna(value):
                        data[key][subkey] = None
                    elif isinstance(value, (np.int64, np.float64)):
                        data[key][subkey] = float(value)
            return data
        
        financial_data = {
            "income_statement": clean_financial_data(income_statement),
            "balance_sheet": clean_financial_data(balance_sheet),
            "cash_flow": clean_financial_data(cashflow),
            "symbol": symbol.upper()
        }
        
        return {"status": "success", "data": financial_data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error fetching financials: {str(e)}")

@app.get("/api/stock/{symbol}/earnings")
async def get_earnings(symbol: str):
    """Get earnings data"""
    try:
        ticker = yf.Ticker(symbol.upper())
        
        # Get earnings data
        quarterly_earnings = ticker.quarterly_earnings
        yearly_earnings = ticker.earnings
        
        earnings_data = {
            "quarterly_earnings": quarterly_earnings.to_dict() if not quarterly_earnings.empty else {},
            "yearly_earnings": yearly_earnings.to_dict() if not yearly_earnings.empty else {},
            "symbol": symbol.upper()
        }
        
        return {"status": "success", "data": earnings_data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error fetching earnings: {str(e)}")

@app.get("/api/stock/{symbol}/history")
async def get_stock_history(symbol: str, period: str = "1y"):
    """Get historical stock price data"""
    try:
        ticker = yf.Ticker(symbol.upper())
        hist = ticker.history(period=period)
        
        if hist.empty:
            raise HTTPException(status_code=404, detail="No data found for symbol")
        
        # Convert to dictionary
        hist_data = {
            "dates": hist.index.strftime("%Y-%m-%d").tolist(),
            "open": hist["Open"].tolist(),
            "high": hist["High"].tolist(),
            "low": hist["Low"].tolist(),
            "close": hist["Close"].tolist(),
            "volume": hist["Volume"].tolist(),
            "symbol": symbol.upper()
        }
        
        return {"status": "success", "data": hist_data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error fetching history: {str(e)}")

@app.post("/api/stock/predict")
async def predict_stock_price(request: PredictionRequest):
    """Predict future stock prices using Prophet"""
    try:
        symbol = request.symbol.upper()
        forecast_days = request.forecast_days
        
        # Get historical data (2 years for better trend analysis)
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="2y")
        
        if hist.empty or len(hist) < 30:
            raise HTTPException(status_code=404, detail="Insufficient historical data for prediction")
        
        # Prepare data for Prophet
        df = hist.reset_index()
        df["Date"] = df["Date"].dt.tz_localize(None)  # Remove timezone info
        df = df[["Date", "Close"]].rename(columns={"Date": "ds", "Close": "y"})
        
        # Initialize and fit Prophet model
        model = Prophet(
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=True,
            changepoint_prior_scale=0.05,
            seasonality_prior_scale=10.0,
            interval_width=0.95
        )
        
        model.fit(df)
        
        # Make future dataframe
        future = model.make_future_dataframe(periods=forecast_days)
        forecast = model.predict(future)
        
        # Extract prediction results
        last_date = df["ds"].iloc[-1]
        future_forecast = forecast[forecast["ds"] > last_date]
        
        prediction_data = {
            "symbol": symbol,
            "forecast_days": forecast_days,
            "last_actual_price": float(df["y"].iloc[-1]),
            "last_date": last_date.strftime("%Y-%m-%d"),
            "predictions": {
                "dates": future_forecast["ds"].dt.strftime("%Y-%m-%d").tolist(),
                "predicted_prices": future_forecast["yhat"].tolist(),
                "lower_bound": future_forecast["yhat_lower"].tolist(),
                "upper_bound": future_forecast["yhat_upper"].tolist(),
            },
            "historical_fit": {
                "dates": df["ds"].dt.strftime("%Y-%m-%d").tolist(),
                "actual_prices": df["y"].tolist(),
                "fitted_prices": forecast[forecast["ds"] <= last_date]["yhat"].tolist()
            }
        }
        
        return {"status": "success", "data": prediction_data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error in prediction: {str(e)}")
    
@app.get("/api/stock/{symbol}/key-metrics")
async def get_key_metrics(symbol: str):
    """Get key financial metrics and ratios"""
    try:
        ticker = yf.Ticker(symbol.upper())
        info = ticker.info
        
        metrics = {
            "symbol": symbol.upper(),
            "valuation_metrics": {
                "market_cap": info.get("marketCap", 0),
                "enterprise_value": info.get("enterpriseValue", 0),
                "pe_ratio": info.get("trailingPE", 0),
                "forward_pe": info.get("forwardPE", 0),
                "peg_ratio": info.get("pegRatio", 0),
                "price_to_book": info.get("priceToBook", 0),
                "price_to_sales": info.get("priceToSalesTrailing12Months", 0),
                "ev_to_revenue": info.get("enterpriseToRevenue", 0),
                "ev_to_ebitda": info.get("enterpriseToEbitda", 0),
            },
            "profitability_metrics": {
                "gross_margins": info.get("grossMargins", 0),
                "operating_margins": info.get("operatingMargins", 0),
                "profit_margins": info.get("profitMargins", 0),
                "return_on_assets": info.get("returnOnAssets", 0),
                "return_on_equity": info.get("returnOnEquity", 0),
            },
            "financial_health": {
                "total_cash": info.get("totalCash", 0),
                "total_debt": info.get("totalDebt", 0),
                "debt_to_equity": info.get("debtToEquity", 0),
                "current_ratio": info.get("currentRatio", 0),
                "quick_ratio": info.get("quickRatio", 0),
            },
            "growth_metrics": {
                "revenue_growth": info.get("revenueGrowth", 0),
                "earnings_growth": info.get("earningsGrowth", 0),
            },
            "dividend_metrics": {
                "dividend_yield": info.get("dividendYield", 0),
                "payout_ratio": info.get("payoutRatio", 0),
                "five_year_avg_dividend_yield": info.get("fiveYearAvgDividendYield", 0),
            }
        }
        
        return {"status": "success", "data": metrics}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error fetching key metrics: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)