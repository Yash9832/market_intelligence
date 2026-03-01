import pandas as pd
import numpy as np
from prophet import Prophet
from typing import Optional, Dict, Any, List
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.schemas import PredictionData
from services.stock_service import StockService

logger = logging.getLogger(__name__)

class PredictionService:
    """Service for handling stock price predictions"""
    
    @staticmethod
    def predict_stock_price(symbol: str, forecast_days: int = 30) -> Optional[PredictionData]:
        """Predict stock prices using Prophet model"""
        try:
            logger.info(f"Starting prediction for {symbol} with {forecast_days} days")
            import yfinance as yf
            
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="2y")
            
            if hist.empty or len(hist) < 30:
                logger.warning(f"Insufficient data for prediction: {symbol}")
                return None

            logger.info(f"Retrieved {len(hist)} data points for {symbol}")
            
            # Prepare data for Prophet
            df = hist.reset_index()
            df["Date"] = df["Date"].dt.tz_localize(None)  # Remove timezone info
            df = df[["Date", "Close"]].rename(columns={"Date": "ds", "Close": "y"})
            
            logger.info(f"Prepared data for Prophet model")
            
            # Initialize and fit Prophet model
            model = Prophet(
                daily_seasonality=True,
                weekly_seasonality=True,
                yearly_seasonality=True,
                changepoint_prior_scale=0.05,
                interval_width=0.95
            )
            
            logger.info(f"Fitting Prophet model...")
            model.fit(df)
            logger.info(f"Prophet model fitted successfully")
            
            # Make future predictions - ensure forecast_days is an integer
            future = model.make_future_dataframe(periods=int(forecast_days))
            logger.info(f"Making predictions for {int(forecast_days)} days...")
            forecast = model.predict(future)
            logger.info(f"Predictions completed successfully")
            
            # Get current and predicted prices
            current_price = float(df['y'].iloc[-1])
            future_predictions = forecast[forecast['ds'] > df['ds'].iloc[-1]]
            
            if future_predictions.empty:
                logger.warning(f"No future predictions generated for {symbol}")
                return None
            
            final_prediction = float(future_predictions['yhat'].iloc[-1])
            confidence_lower = float(future_predictions['yhat_lower'].iloc[-1])
            confidence_upper = float(future_predictions['yhat_upper'].iloc[-1])
            
            price_change = final_prediction - current_price
            price_change_percent = (price_change / current_price) * 100
            
            # Get short-term predictions
            day_1_pred = float(future_predictions['yhat'].iloc[0]) if len(future_predictions) >= 1 else final_prediction
            week_1_pred = float(future_predictions['yhat'].iloc[6]) if len(future_predictions) >= 7 else final_prediction
            month_1_pred = float(future_predictions['yhat'].iloc[29]) if len(future_predictions) >= 30 else final_prediction
            
            # Format predictions for response
            predictions = []
            for _, row in future_predictions.iterrows():
                predictions.append({
                    'date': row['ds'].strftime('%Y-%m-%d'),
                    'predicted_price': round(float(row['yhat']), 2),
                    'lower_bound': round(float(row['yhat_lower']), 2),
                    'upper_bound': round(float(row['yhat_upper']), 2)
                })
            
            logger.info(f"Prediction completed for {symbol}: current={current_price}, predicted={final_prediction}")
            
            return PredictionData(
                symbol=symbol,
                forecast_days=forecast_days,
                current_price=current_price,
                predicted_price=final_prediction,
                confidence_lower=confidence_lower,
                confidence_upper=confidence_upper,
                price_change=price_change,
                price_change_percent=price_change_percent,
                predictions=predictions,
                day_1=day_1_pred,
                week_1=week_1_pred,
                month_1=month_1_pred,
                confidence={
                    'day_1': 0.85,
                    'week_1': 0.75,
                    'month_1': 0.65
                }
            )
            
        except Exception as e:
            logger.error(f"Error predicting stock price for {symbol}: {str(e)}", exc_info=True)
            return None
    
    @staticmethod
    def calculate_technical_indicators(symbol: str, period: str = "1y") -> Optional[Dict[str, Any]]:
        """Calculate technical indicators"""
        try:
            import yfinance as yf
            
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            
            if hist.empty or len(hist) < 50:
                return None
            
            # Calculate moving averages
            hist['MA20'] = hist['Close'].rolling(window=20).mean()
            hist['MA50'] = hist['Close'].rolling(window=50).mean()
            
            # Calculate RSI
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            current_price = float(hist['Close'].iloc[-1])
            ma20 = float(hist['MA20'].iloc[-1]) if not pd.isna(hist['MA20'].iloc[-1]) else None
            ma50 = float(hist['MA50'].iloc[-1]) if not pd.isna(hist['MA50'].iloc[-1]) else None
            current_rsi = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else None
            
            # Determine signals
            rsi_signal = "Overbought" if current_rsi and current_rsi > 70 else "Oversold" if current_rsi and current_rsi < 30 else "Neutral"
            ma_signal = "Above MA20" if ma20 and current_price > ma20 else "Below MA20"
            
            volume_avg = float(hist['Volume'].rolling(window=20).mean().iloc[-1])
            current_volume = float(hist['Volume'].iloc[-1])
            volume_signal = "High Volume" if current_volume > volume_avg else "Low Volume"
            
            return {
                'rsi': current_rsi,
                'ma20': ma20,
                'ma50': ma50,
                'current_price': current_price,
                'rsi_signal': rsi_signal,
                'ma_signal': ma_signal,
                'volume_signal': volume_signal,
                'volume': current_volume,
                'volume_avg': volume_avg
            }
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators for {symbol}: {str(e)}")
            return None