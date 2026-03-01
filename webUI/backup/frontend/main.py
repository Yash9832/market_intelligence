import streamlit as st
from streamlit_autorefresh import st_autorefresh
import time

# Import components
from components import (
    create_search_bar, 
    create_quick_access_buttons,
    display_market_overview,
    display_market_movers,
    display_market_news,
    display_watchlist,
    StockAnalyzer
)

# Configure Streamlit page
st.set_page_config(
    page_title="🚀 Financial Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-message {
        color: #28a745;
        font-weight: bold;
    }
    .error-message {
        color: #dc3545;
        font-weight: bold;
    }
    .info-box {
        background-color: #e3f2fd;
        padding: 1rem;
        border-left: 4px solid #1976d2;
        margin: 1rem 0;
    }
    .sidebar .sidebar-content {
        padding-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'selected_stock' not in st.session_state:
        st.session_state.selected_stock = None
    if 'watchlist' not in st.session_state:
        st.session_state.watchlist = ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
    if 'auto_refresh' not in st.session_state:
        st.session_state.auto_refresh = False

def main():
    """Main application function"""
    initialize_session_state()
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Auto-refresh option
        auto_refresh = st.checkbox("🔄 Auto-refresh (30s)", value=st.session_state.auto_refresh)
        st.session_state.auto_refresh = auto_refresh
        
        if auto_refresh:
            # Auto-refresh every 30 seconds
            count = st_autorefresh(interval=30000, key="datarefresh")
            st.write(f"Last update: {time.strftime('%H:%M:%S')}")
        
        st.markdown("---")
        
        # Navigation
        st.header("🧭 Navigation")
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.selected_stock = None
        
        if st.session_state.selected_stock:
            if st.button("📊 Back to Analysis", use_container_width=True):
                pass  # Stay on analysis page
        
        st.markdown("---")
        
        # Display watchlist in sidebar
        display_watchlist()
    
    # Main content area
    if st.session_state.selected_stock:
        # Show stock analysis
        analyzer = StockAnalyzer(st.session_state.selected_stock)
        analyzer.display()
        
        # Option to go back to home
        if st.button("⬅️ Back to Market Overview"):
            st.session_state.selected_stock = None
            st.rerun()
    
    else:
        # Show landing page
        display_landing_page()

def display_landing_page():
    """Display the main landing page"""
    # Search bar at the top
    selected_stock = create_search_bar()
    
    if selected_stock:
        st.session_state.selected_stock = selected_stock
        st.rerun()
    
    # Quick access buttons
    quick_stock = create_quick_access_buttons()
    if quick_stock:
        st.session_state.selected_stock = quick_stock
        st.rerun()
    
    st.markdown("---")
    
    # Market overview section
    display_market_overview()
    
    st.markdown("---")
    
    # Market movers section
    display_market_movers()
    
    st.markdown("---")
    
    # Market news section
    display_market_news()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 2rem;'>
        <p>🚀 Financial Dashboard - Real-time market analysis and predictions</p>
        <p><small>Data provided by Yahoo Finance | Predictions by Prophet ML</small></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()