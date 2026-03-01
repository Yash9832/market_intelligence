import streamlit as st
from typing import Optional, List, Dict, Any
import sys
import os

# Add parent directory to path for imports  
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.api_client import call_api, cached_api_call

def create_search_bar() -> Optional[str]:
    """Create search bar component with suggestions"""
    
    # Custom CSS for search bar
    st.markdown("""
    <style>
        .search-container {
            background: linear-gradient(90deg, #1f77b4, #ff7f0e);
            padding: 2rem;
            border-radius: 1rem;
            margin-bottom: 2rem;
        }
        .search-title {
            color: white;
            font-size: 2rem;
            font-weight: bold;
            text-align: center;
            margin-bottom: 1rem;
        }
        .search-subtitle {
            color: rgba(255, 255, 255, 0.9);
            text-align: center;
            margin-bottom: 1.5rem;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Search container
    st.markdown("""
    <div class="search-container">
        <div class="search-title">🚀 Financial Dashboard</div>
        <div class="search-subtitle">Search and analyze stocks, get predictions, and track market trends</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Search input
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col2:
        search_query = st.text_input(
            "",
            placeholder="Search for stocks (e.g., AAPL, Tesla, Microsoft)...",
            key="stock_search",
            label_visibility="collapsed"
        )
        
        search_button = st.button("🔍 Search Stock", type="primary", use_container_width=True)
    
    # Handle search
    if search_button and search_query:
        return search_query.upper().strip()
    
    # Show suggestions
    if search_query and len(search_query) >= 2:
        with col2:
            with st.spinner("Searching..."):
                # Try API first
                response = cached_api_call(f"/stocks/search", f"{{'query': '{search_query}', 'limit': 5}}")
                
                if response and response.get("success"):
                    results = response.get("data", {}).get("results", [])
                    
                    if results:
                        st.markdown("**Suggestions:**")
                        for result in results[:5]:
                            if st.button(f"📊 {result['symbol']} - {result['name']}", key=f"suggest_{result['symbol']}"):
                                return result['symbol']
                else:
                    # Fallback suggestions
                    common_stocks = [
                        {"symbol": "AAPL", "name": "Apple Inc."},
                        {"symbol": "GOOGL", "name": "Alphabet Inc."},
                        {"symbol": "MSFT", "name": "Microsoft Corporation"},
                        {"symbol": "TSLA", "name": "Tesla, Inc."},
                    ]
                    
                    filtered = [s for s in common_stocks if search_query.lower() in s['symbol'].lower() or search_query.lower() in s['name'].lower()]
                    
                    if filtered:
                        st.markdown("**Suggestions:**")
                        for stock in filtered[:3]:
                            if st.button(f"📊 {stock['symbol']} - {stock['name']}", key=f"fallback_{stock['symbol']}"):
                                return stock['symbol']
    
    return None

def create_quick_access_buttons():
    """Create quick access buttons for popular stocks"""
    st.markdown("### 🔥 Popular Stocks")
    
    popular_stocks = [
        {"symbol": "AAPL", "name": "Apple", "icon": "🍎"},
        {"symbol": "GOOGL", "name": "Google", "icon": "🔍"},
        {"symbol": "TSLA", "name": "Tesla", "icon": "🚗"},
        {"symbol": "MSFT", "name": "Microsoft", "icon": "💻"},
        {"symbol": "RELIANCE.NS", "name": "Reliance", "icon": "🏭"},
        {"symbol": "TCS.NS", "name": "TCS", "icon": "💼"}
    ]
    
    cols = st.columns(6)
    selected_stock = None
    
    for i, stock in enumerate(popular_stocks):
        with cols[i]:
            if st.button(
                f"{stock['icon']}\n{stock['name']}\n`{stock['symbol']}`",
                key=f"popular_{stock['symbol']}",
                help=f"Analyze {stock['name']} ({stock['symbol']})"
            ):
                selected_stock = stock['symbol']
    
    return selected_stock