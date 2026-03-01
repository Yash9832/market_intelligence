import yfinance as yf
import pandas as pd
import numpy as np
from typing import Optional, Tuple, Dict, Any, List
from datetime import datetime, timedelta
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.schemas import StockData, CompanyInfo, HistoricalData, FinancialMetrics

logger = logging.getLogger(__name__)

class StockService:
    """Service for handling stock data operations"""
    
    @staticmethod
    def get_stock_info(symbol: str) -> Tuple[Optional[StockData], Optional[CompanyInfo]]:
        """Get basic stock data and company info"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period="2d")
            
            if hist.empty or len(hist) < 2:
                logger.warning(f"Insufficient historical data for {symbol}")
                return None, None
            
            current_price = float(hist['Close'].iloc[-1])
            prev_close = float(hist['Close'].iloc[-2])
            price_change = current_price - prev_close
            price_change_pct = (price_change / prev_close) * 100
            
            # Stock data
            stock_data = StockData(
                symbol=symbol,
                current_price=current_price,
                price_change=price_change,
                price_change_percent=price_change_pct,
                volume=int(hist['Volume'].iloc[-1]),
                market_cap=info.get('marketCap'),
                pe_ratio=info.get('trailingPE'),
                week_52_high=info.get('fiftyTwoWeekHigh'),
                week_52_low=info.get('fiftyTwoWeekLow')
            )
            
            # Company info
            company_info = CompanyInfo(
                symbol=symbol,
                name=info.get('longName'),
                sector=info.get('sector'),
                industry=info.get('industry'),
                country=info.get('country'),
                website=info.get('website'),
                employees=info.get('fullTimeEmployees'),
                description=info.get('longBusinessSummary')
            )
            
            return stock_data, company_info
            
        except Exception as e:
            logger.error(f"Error fetching stock info for {symbol}: {str(e)}")
            return None, None
    
    @staticmethod
    def get_historical_data(symbol: str, period: str = "1y") -> Optional[HistoricalData]:
        """Get historical stock data"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            
            if hist.empty:
                return None
            
            return HistoricalData(
                dates=[date.strftime('%Y-%m-%d') for date in hist.index],
                open=[float(price) for price in hist['Open'].tolist()],
                high=[float(price) for price in hist['High'].tolist()],
                low=[float(price) for price in hist['Low'].tolist()],
                close=[float(price) for price in hist['Close'].tolist()],
                volume=[int(vol) for vol in hist['Volume'].tolist()]
            )
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {str(e)}")
            return None
    
    @staticmethod
    def get_financial_metrics(symbol: str) -> Optional[FinancialMetrics]:
        """Get detailed financial metrics"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return FinancialMetrics(
                market_cap=info.get('marketCap'),
                enterprise_value=info.get('enterpriseValue'),
                pe_ratio=info.get('trailingPE'),
                forward_pe=info.get('forwardPE'),
                price_to_book=info.get('priceToBook'),
                gross_margin=info.get('grossMargins'),
                operating_margin=info.get('operatingMargins'),
                profit_margin=info.get('profitMargins'),
                roe=info.get('returnOnEquity'),
                roa=info.get('returnOnAssets'),
                total_cash=info.get('totalCash'),
                total_debt=info.get('totalDebt'),
                debt_to_equity=info.get('debtToEquity'),
                current_ratio=info.get('currentRatio'),
                quick_ratio=info.get('quickRatio')
            )
            
        except Exception as e:
            logger.error(f"Error fetching financial metrics for {symbol}: {str(e)}")
            return None
    
    @staticmethod
    def search_stocks(query: str, limit: int = 10) -> List[Dict[str, str]]:
        """Search for stocks by company name or symbol"""
        # This is a simplified search - in production, you'd use a proper search API
        try:
            # Common stock symbols for demonstration
            common_stocks = {
                'AAPL': 'Apple Inc.',
                'GOOGL': 'Alphabet Inc.',
                'MSFT': 'Microsoft Corporation',
                'TSLA': 'Tesla, Inc.',
                'AMZN': 'Amazon.com, Inc.',
                'NVDA': 'NVIDIA Corporation',
                'META': 'Meta Platforms, Inc.',
                'RELIANCE.NS': 'Reliance Industries Limited',
                'TCS.NS': 'Tata Consultancy Services',
                'INFY.NS': 'Infosys Limited',
                'HDFCBANK.NS': 'HDFC Bank Limited',
                'ICICIBANK.NS': 'ICICI Bank Limited'
            }
            
            results = []
            query_lower = query.lower()
            
            for symbol, name in common_stocks.items():
                if (query_lower in symbol.lower() or 
                    query_lower in name.lower()):
                    results.append({
                        'symbol': symbol,
                        'name': name
                    })
                
                if len(results) >= limit:
                    break
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching stocks: {str(e)}")
            return []
    
    @staticmethod
    def get_technical_analysis(symbol: str, period: str = "3mo") -> Optional[Dict[str, Any]]:
        """Get technical analysis data for charts"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Get historical data
            hist = ticker.history(period=period)
            
            if hist.empty:
                return None
            
            # Convert to serializable format
            chart_data = []
            for date, row in hist.iterrows():
                chart_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': int(row['Volume'])
                })
            
            # Calculate basic technical indicators
            closes = hist['Close'].values
            
            # Simple moving averages
            sma_10 = hist['Close'].rolling(window=10).mean()
            sma_20 = hist['Close'].rolling(window=20).mean()
            
            # Price performance
            first_price = float(closes[0])
            last_price = float(closes[-1])
            total_return = ((last_price - first_price) / first_price) * 100
            
            # Volatility (standard deviation of returns)
            returns = hist['Close'].pct_change().dropna()
            volatility = float(returns.std() * 100)
            
            return {
                'symbol': symbol,
                'period': period,
                'chart_data': chart_data,
                'total_return': round(total_return, 2),
                'volatility': round(volatility, 2),
                'sma_10': sma_10.dropna().iloc[-1:].tolist(),
                'sma_20': sma_20.dropna().iloc[-1:].tolist(),
                'current_price': float(last_price),
                'period_high': float(hist['High'].max()),
                'period_low': float(hist['Low'].min()),
                'trading_volume': int(hist['Volume'].mean())
            }
            
        except Exception as e:
            logger.error(f"Error getting technical analysis for {symbol}: {str(e)}")
            return None