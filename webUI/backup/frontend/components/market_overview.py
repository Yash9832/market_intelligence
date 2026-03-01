import streamlit as st
from typing import Dict, List, Any
import sys
import os

# Add parent directory to path for imports  
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.api_client import call_api, format_currency, get_price_change_color, get_price_change_arrow
from utils.chart_utils import create_market_overview_chart

def display_market_overview():
    """Display market overview with indices"""
    st.markdown("### 📊 Market Overview")
    
    # Get market indices data
    with st.spinner("Loading market data..."):
        response = call_api("/market/indices")
        
        if response and response.get("success"):
            indices_data = response.get("data", {}).get("indices", [])
            
            if indices_data:
                # Display indices in cards
                cols = st.columns(min(4, len(indices_data)))
                
                for i, index in enumerate(indices_data[:8]):  # Show max 8 indices
                    col_idx = i % 4
                    with cols[col_idx]:
                        color = get_price_change_color(index['change_percent'])
                        arrow = get_price_change_arrow(index['change_percent'])
                        
                        currency_symbol = "$" if index.get('currency') == 'USD' else "₹"
                        
                        st.markdown(f"""
                        <div style='background:#222;padding:20px;border-radius:16px;color:#fff;text-align:center;margin-bottom:10px;'>
                            <span style='font-size:18px;font-weight:bold;'>{index['name']}</span><br>
                            <span style='color:{color};font-size:14px;'>{arrow} {abs(index['change_percent']):.2f}%</span><br>
                            <span style='font-size:24px;'>{currency_symbol}{index['price']:,.2f}</span>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Create market overview chart
                if len(indices_data) > 3:
                    chart = create_market_overview_chart(indices_data[:6])
                    if chart:
                        st.plotly_chart(chart, use_container_width=True)
            
        else:
            # Fallback to basic display
            st.info("📡 Market data temporarily unavailable")

def display_market_movers():
    """Display top gainers and losers"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📈 Top Gainers")
        display_movers("gainers", "US")
    
    with col2:
        st.markdown("### 📉 Top Losers") 
        display_movers("losers", "US")

def display_movers(category: str, market: str = "US", limit: int = 5):
    """Display market movers in a category"""
    response = call_api(f"/market/movers", {"category": category, "market": market, "limit": limit})
    
    if response and response.get("success"):
        movers = response.get("data", {}).get("movers", [])
        
        for mover in movers:
            color = get_price_change_color(mover['change_percent'])
            
            st.markdown(f"""
            <div style='padding:8px;border-bottom:1px solid #333;display:flex;justify-content:space-between;'>
                <div>
                    <strong>{mover['symbol']}</strong><br>
                    <small style='color:#888;'>{mover['name'][:30]}...</small>
                </div>
                <div style='text-align:right;'>
                    <div>${mover['price']:.2f}</div>
                    <div style='color:{color};'>{mover['change_percent']:.2f}%</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info(f"Unable to load {category} data")

def display_market_news():
    """Display market news section"""
    st.markdown("### 📰 Market News")
    
    # Sample news - in production, integrate with news API
    news_items = [
        {
            "title": "Tech Stocks Rally on AI Optimism",
            "summary": "Major technology companies see gains as investors show confidence in artificial intelligence developments...",
            "time": "2 hours ago"
        },
        {
            "title": "Federal Reserve Maintains Interest Rates",
            "summary": "The Fed keeps rates steady while monitoring inflation indicators and employment data...",
            "time": "4 hours ago"
        },
        {
            "title": "Energy Sector Shows Mixed Results",
            "summary": "Oil prices fluctuate amid global supply chain adjustments and geopolitical tensions...",
            "time": "6 hours ago"
        }
    ]
    
    for news in news_items:
        st.markdown(f"""
        <div style='background:#181818;padding:15px;border-radius:10px;margin-bottom:10px;'>
            <h4 style='margin:0;color:#fff;'>{news['title']}</h4>
            <p style='margin:5px 0;color:#ccc;'>{news['summary']}</p>
            <small style='color:#888;'>{news['time']}</small>
        </div>
        """, unsafe_allow_html=True)

def display_watchlist():
    """Display user watchlist"""
    st.markdown("### ⭐ Watchlist")
    
    # Sample watchlist - in production, would be user-specific
    if 'watchlist' not in st.session_state:
        st.session_state.watchlist = ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
    
    if st.session_state.watchlist:
        for symbol in st.session_state.watchlist:
            # Get basic stock info
            response = call_api(f"/stocks/{symbol}/info")
            
            if response and response.get("success"):
                stock_data = response.get("data", {}).get("stock_data", {})
                color = get_price_change_color(stock_data.get('price_change_percent', 0))
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{symbol}** - ${stock_data.get('current_price', 0):.2f}")
                with col2:
                    if st.button("📊", key=f"watch_{symbol}", help="Analyze"):
                        st.session_state.selected_stock = symbol
                        st.rerun()
    
    # Add to watchlist
    new_symbol = st.text_input("Add to watchlist", placeholder="Enter symbol")
    if st.button("Add") and new_symbol:
        if new_symbol.upper() not in st.session_state.watchlist:
            st.session_state.watchlist.append(new_symbol.upper())
            st.success(f"Added {new_symbol.upper()} to watchlist")
            st.rerun()