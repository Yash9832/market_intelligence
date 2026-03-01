import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import streamlit as st
from typing import Dict, Any, List

def create_candlestick_chart(data: Dict[str, List], symbol: str):
    """Create candlestick chart from historical data"""
    try:
        df = pd.DataFrame({
            'Date': pd.to_datetime(data['dates']),
            'Open': data['open'],
            'High': data['high'],
            'Low': data['low'],
            'Close': data['close'],
            'Volume': data['volume']
        })
        df.set_index('Date', inplace=True)
        
        fig = go.Figure(data=go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name=symbol
        ))
        
        fig.update_layout(
            title=f"{symbol} Stock Price",
            xaxis_title="Date",
            yaxis_title="Price ($)",
            height=500,
            showlegend=False,
            xaxis_rangeslider_visible=False
        )
        
        return fig
    except Exception as e:
        st.error(f"Error creating candlestick chart: {str(e)}")
        return None

def create_volume_chart(data: Dict[str, List], symbol: str):
    """Create volume chart from historical data"""
    try:
        df = pd.DataFrame({
            'Date': pd.to_datetime(data['dates']),
            'Volume': data['volume']
        })
        df.set_index('Date', inplace=True)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df.index,
            y=df['Volume'],
            name="Volume",
            marker_color='rgba(55, 128, 191, 0.7)'
        ))
        
        fig.update_layout(
            title=f"{symbol} Trading Volume",
            xaxis_title="Date",
            yaxis_title="Volume",
            height=300,
            showlegend=False
        )
        
        return fig
    except Exception as e:
        st.error(f"Error creating volume chart: {str(e)}")
        return None

def create_prediction_chart(predictions: List[Dict], symbol: str, current_price: float):
    """Create prediction chart from API response"""
    try:
        pred_df = pd.DataFrame(predictions)
        pred_df['date'] = pd.to_datetime(pred_df['date'])
        
        fig = go.Figure()
        
        # Predicted prices
        fig.add_trace(go.Scatter(
            x=pred_df['date'],
            y=pred_df['predicted_price'],
            mode='lines',
            name='Predicted Price',
            line=dict(color='red', dash='dash')
        ))
        
        # Confidence intervals
        fig.add_trace(go.Scatter(
            x=pred_df['date'],
            y=pred_df['upper_bound'],
            fill=None,
            mode='lines',
            line_color='rgba(0,0,0,0)',
            showlegend=False,
            name='Upper Bound'
        ))
        
        fig.add_trace(go.Scatter(
            x=pred_df['date'],
            y=pred_df['lower_bound'],
            fill='tonexty',
            mode='lines',
            line_color='rgba(0,0,0,0)',
            name='Confidence Interval',
            fillcolor='rgba(255,0,0,0.2)'
        ))
        
        # Current price line
        fig.add_hline(
            y=current_price,
            line_dash="solid",
            line_color="blue",
            annotation_text=f"Current Price: ${current_price:.2f}"
        )
        
        fig.update_layout(
            title=f"{symbol} Price Prediction",
            xaxis_title="Date",
            yaxis_title="Price ($)",
            height=500,
            hovermode='x unified'
        )
        
        return fig
    except Exception as e:
        st.error(f"Error creating prediction chart: {str(e)}")
        return None

def create_technical_analysis_chart(historical_data: Dict, technical_data: Dict, symbol: str):
    """Create technical analysis chart with moving averages and RSI"""
    try:
        df = pd.DataFrame({
            'Date': pd.to_datetime(historical_data['dates']),
            'Close': historical_data['close']
        })
        df.set_index('Date', inplace=True)
        
        # Calculate moving averages
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA50'] = df['Close'].rolling(window=50).mean()
        
        # Calculate RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Price with Moving Averages', 'RSI'),
            vertical_spacing=0.1,
            row_heights=[0.7, 0.3]
        )
        
        # Price and moving averages
        fig.add_trace(
            go.Scatter(x=df.index, y=df['Close'], name='Close Price', line=dict(color='blue')),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df.index, y=df['MA20'], name='MA20', line=dict(color='orange')),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df.index, y=df['MA50'], name='MA50', line=dict(color='red')),
            row=1, col=1
        )
        
        # RSI
        fig.add_trace(
            go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='purple')),
            row=2, col=1
        )
        
        # RSI reference lines
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
        
        fig.update_layout(height=600, title_text=f"{symbol} Technical Analysis")
        fig.update_yaxes(title_text="Price ($)", row=1, col=1)
        fig.update_yaxes(title_text="RSI", row=2, col=1)
        
        return fig
    except Exception as e:
        st.error(f"Error creating technical analysis chart: {str(e)}")
        return None

def create_market_overview_chart(indices_data: List[Dict]):
    """Create market overview chart"""
    try:
        df = pd.DataFrame(indices_data)
        
        fig = px.bar(
            df,
            x='name',
            y='change_percent',
            color='change_percent',
            color_continuous_scale=['red', 'green'],
            title="Market Indices Performance",
            labels={'change_percent': 'Change %', 'name': 'Index'}
        )
        
        fig.update_layout(
            height=400,
            showlegend=False,
            xaxis_tickangle=-45
        )
        
        return fig
    except Exception as e:
        st.error(f"Error creating market overview chart: {str(e)}")
        return None