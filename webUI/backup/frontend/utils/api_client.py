import requests
import streamlit as st
from typing import Optional, Dict, Any, List
import pandas as pd
import yfinance as yf

# API Configuration
API_BASE_URL = "http://localhost:8000"

def call_api(endpoint: str, params: Dict = None) -> Optional[Dict[str, Any]]:
    """Make API call with error handling"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code}")
            return None
            
    except requests.exceptions.ConnectionError:
        return None
    except requests.exceptions.Timeout:
        st.error("Request timed out")
        return None
    except Exception as e:
        st.error(f"API request failed: {str(e)}")
        return None

def check_api_status() -> bool:
    """Check if API is available"""
    response = call_api("/health")
    return response is not None and response.get("success", False)

def get_stock_data_direct(symbol: str, period: str = "1y"):
    """Fallback function to get data directly from yfinance"""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
        info = ticker.info
        return hist, info
    except Exception as e:
        st.error(f"Error fetching stock data: {str(e)}")
        return None, None

def format_number(value):
    """Format large numbers for display"""
    if pd.isna(value) or value == 0:
        return "N/A"
    
    if abs(value) >= 1e12:
        return f"${value/1e12:.2f}T"
    elif abs(value) >= 1e9:
        return f"${value/1e9:.2f}B"
    elif abs(value) >= 1e6:
        return f"${value/1e6:.2f}M"
    elif abs(value) >= 1e3:
        return f"${value/1e3:.2f}K"
    else:
        return f"${value:.2f}"

def format_currency(value: float, currency: str = "USD") -> str:
    """Format currency values"""
    if pd.isna(value):
        return "N/A"
    
    if currency == "INR":
        return f"₹{value:,.2f}"
    elif currency == "USD":
        return f"${value:,.2f}"
    else:
        return f"{value:,.2f}"

def get_price_change_color(change_percent: float) -> str:
    """Get color for price changes"""
    if change_percent > 0:
        return "#5dd99c"  # Green for positive
    elif change_percent < 0:
        return "#e44747"  # Red for negative
    else:
        return "#888888"  # Gray for neutral

def get_price_change_arrow(change_percent: float) -> str:
    """Get arrow for price changes"""
    if change_percent > 0:
        return "↑"
    elif change_percent < 0:
        return "↓"
    else:
        return "→"

@st.cache_data(ttl=300)  # Cache for 5 minutes
def cached_api_call(endpoint: str, params_str: str = "") -> Optional[Dict[str, Any]]:
    """Cached API call to reduce repeated requests"""
    params = eval(params_str) if params_str else None
    return call_api(endpoint, params)