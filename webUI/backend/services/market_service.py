import yfinance as yf
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class MarketService:
    """Service for market overview and index data"""
    
    @staticmethod
    def get_market_indices() -> List[Dict[str, Any]]:
        """Get major market indices data"""
        try:
            indices = {
                "NIFTY 50": "^NSEI",
                "S&P BSE Sensex": "^BSESN",
                "Nifty Bank Index": "^NSEBANK",
                "Bitcoin": "BTC-USD",
                "S&P 500": "^GSPC",
                "NASDAQ": "^IXIC",
                "Dow Jones": "^DJI"
            }
            
            results = []
            for name, ticker in indices.items():
                try:
                    stock = yf.Ticker(ticker)
                    hist = stock.history(period="2d")
                    if len(hist) >= 2:
                        latest_close = float(hist['Close'].iloc[-1])
                        prev_close = float(hist['Close'].iloc[-2])
                        change_pct = ((latest_close - prev_close) / prev_close) * 100
                        change_value = latest_close - prev_close
                        
                        # Determine currency: INR for Indian indices, USD for US indices and BTC
                        if ticker in {"^NSEI", "^BSESN", "^NSEBANK"}:
                            currency = 'INR'
                        elif ticker in {"^GSPC", "^IXIC", "^DJI"} or name == 'Bitcoin':
                            currency = 'USD'
                        else:
                            # Fallback: NSE (.NS) and BSE (.BO) equities in INR, others USD
                            currency = 'INR' if symbol.endswith('.NS') or symbol.endswith('.BO') else 'USD'

                        results.append({
                            'name': name,
                            'symbol': ticker,
                            'price': round(latest_close, 2),
                            'change': round(change_value, 2),
                            'change_percent': round(change_pct, 2),
                            'currency': currency
                        })
                except Exception as e:
                    logger.warning(f"Failed to fetch data for {name}: {str(e)}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"Error fetching market indices: {str(e)}")
            return []
    
    @staticmethod
    def get_market_movers(category: str = "gainers", market: str = "US", limit: int = 10) -> List[Dict[str, Any]]:
        """Get market movers (gainers/losers)"""
        try:
            # Sample data - in production, you'd use a real market data API
            if category == "gainers":
                if market == "US":
                    symbols = ["AAPL", "TSLA", "NVDA", "GOOGL", "MSFT", "AMZN", "META"]
                else:  # India
                    symbols = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]
            else:  # losers
                if market == "US":
                    symbols = ["NFLX", "PYPL", "SHOP", "SQ", "ZM"]
                else:  # India
                    symbols = ["WIPRO.NS", "LTI.NS", "TECHM.NS"]
            
            results = []
            for symbol in symbols[:limit]:
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period="2d")
                    info = ticker.info
                    
                    if len(hist) >= 2:
                        latest_close = float(hist['Close'].iloc[-1])
                        prev_close = float(hist['Close'].iloc[-2])
                        change_pct = ((latest_close - prev_close) / prev_close) * 100
                        
                        # Filter based on category
                        if (category == "gainers" and change_pct > 0) or (category == "losers" and change_pct < 0):
                            results.append({
                                'symbol': symbol,
                                'name': info.get('longName', symbol),
                                'price': round(latest_close, 2),
                                'change_percent': round(change_pct, 2),
                                'volume': int(hist['Volume'].iloc[-1])
                            })
                            
                except Exception as e:
                    logger.warning(f"Failed to fetch data for {symbol}: {str(e)}")
                    continue
            
            # Sort by change percentage
            if category == "gainers":
                results.sort(key=lambda x: x['change_percent'], reverse=True)
            else:
                results.sort(key=lambda x: x['change_percent'])
            
            return results
            
        except Exception as e:
            logger.error(f"Error fetching market movers: {str(e)}")
            return []