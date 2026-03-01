import streamlit as st
from typing import Optional, Dict, Any
import pandas as pd
import sys
import os

# Add parent directory to path for imports  
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.api_client import (
    call_api, get_stock_data_direct, format_number
)
from utils.chart_utils import (
    create_candlestick_chart, create_volume_chart, 
    create_prediction_chart, create_technical_analysis_chart
)

class StockAnalyzer:
    """Stock analyzer component for detailed stock analysis"""
    
    def __init__(self, symbol: str):
        self.symbol = symbol.upper()
        self.use_api = self._check_api_status()
    
    def _check_api_status(self) -> bool:
        """Check if API is available"""
        response = call_api("/health")
        return response is not None and response.get("success", False)
    
    def display(self):
        """Display complete stock analysis"""
        st.markdown(f"# 📊 {self.symbol} Analysis")
        
        # Show API status
        if self.use_api:
            st.success("✅ Using API data")
        else:
            st.warning("⚠️ API offline - Using direct data")
        
        # Create tabs for different analysis sections
        tab1, tab2, tab3, tab4 = st.tabs(["📈 Overview", "💰 Financials", "📊 Technical", "🔮 Predictions"])
        
        with tab1:
            self._display_overview()
        
        with tab2:
            self._display_financials()
        
        with tab3:
            self._display_technical_analysis()
        
        with tab4:
            self._display_predictions()
    
    def _display_overview(self):
        """Display stock overview"""
        st.header(f"📈 {self.symbol} Overview")
        
        # Get stock data
        if self.use_api:
            response = call_api(f"/stocks/{self.symbol}/info")
            if response and response.get("success"):
                data = response.get("data", {})
                stock_data = data.get("stock_data", {})
                company_info = data.get("company_info", {})
            else:
                stock_data, company_info = self._get_fallback_data()
        else:
            stock_data, company_info = self._get_fallback_data()
        
        if stock_data:
            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Current Price",
                    f"${stock_data.get('current_price', 0):.2f}",
                    f"${stock_data.get('price_change', 0):.2f} ({stock_data.get('price_change_percent', 0):.2f}%)"
                )
            
            with col2:
                st.metric("Market Cap", format_number(stock_data.get('market_cap', 0)))
            
            with col3:
                st.metric("Volume", f"{stock_data.get('volume', 0):,}")
            
            with col4:
                pe_ratio = stock_data.get('pe_ratio')
                st.metric("P/E Ratio", f"{pe_ratio:.2f}" if pe_ratio else "N/A")
        
        # Company information
        if company_info:
            st.subheader("Company Information")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Name:** {company_info.get('name', 'N/A')}")
                st.write(f"**Sector:** {company_info.get('sector', 'N/A')}")
                st.write(f"**Industry:** {company_info.get('industry', 'N/A')}")
            
            with col2:
                st.write(f"**Country:** {company_info.get('country', 'N/A')}")
                employees = company_info.get('employees')
                st.write(f"**Employees:** {employees:,}" if employees else "**Employees:** N/A")
                website = company_info.get('website')
                if website:
                    st.markdown(f"**Website:** [{website}]({website})")
        
        # Charts
        self._display_price_charts()
    
    def _display_financials(self):
        """Display financial metrics"""
        st.header(f"💰 {self.symbol} Financials")
        
        if self.use_api:
            response = call_api(f"/stocks/{self.symbol}/financials")
            if response and response.get("success"):
                financial_data = response.get("data", {})
            else:
                financial_data = None
        else:
            financial_data = None
        
        if financial_data:
            # Display financial metrics in columns
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**Valuation Metrics**")
                st.write(f"Market Cap: {format_number(financial_data.get('market_cap', 0))}")
                st.write(f"Enterprise Value: {format_number(financial_data.get('enterprise_value', 0))}")
                st.write(f"P/E Ratio: {financial_data.get('pe_ratio', 'N/A')}")
                st.write(f"Forward P/E: {financial_data.get('forward_pe', 'N/A')}")
                st.write(f"Price to Book: {financial_data.get('price_to_book', 'N/A')}")
            
            with col2:
                st.markdown("**Profitability**")
                gross_margin = financial_data.get('gross_margin')
                st.write(f"Gross Margin: {gross_margin:.2%}" if gross_margin else "Gross Margin: N/A")
                operating_margin = financial_data.get('operating_margin')
                st.write(f"Operating Margin: {operating_margin:.2%}" if operating_margin else "Operating Margin: N/A")
                profit_margin = financial_data.get('profit_margin')
                st.write(f"Profit Margin: {profit_margin:.2%}" if profit_margin else "Profit Margin: N/A")
                roe = financial_data.get('roe')
                st.write(f"ROE: {roe:.2%}" if roe else "ROE: N/A")
                roa = financial_data.get('roa')
                st.write(f"ROA: {roa:.2%}" if roa else "ROA: N/A")
            
            with col3:
                st.markdown("**Financial Health**")
                st.write(f"Total Cash: {format_number(financial_data.get('total_cash', 0))}")
                st.write(f"Total Debt: {format_number(financial_data.get('total_debt', 0))}")
                st.write(f"Debt/Equity: {financial_data.get('debt_to_equity', 'N/A')}")
                st.write(f"Current Ratio: {financial_data.get('current_ratio', 'N/A')}")
                st.write(f"Quick Ratio: {financial_data.get('quick_ratio', 'N/A')}")
        else:
            st.info("Financial data not available")
    
    def _display_technical_analysis(self):
        """Display technical analysis"""
        st.header(f"📊 {self.symbol} Technical Analysis")
        
        # Get technical indicators
        if self.use_api:
            response = call_api(f"/predictions/{self.symbol}/technical")
            if response and response.get("success"):
                technical_data = response.get("data", {})
                self._display_technical_indicators(technical_data)
        
        # Get historical data for charts
        if self.use_api:
            response = call_api(f"/stocks/{self.symbol}/historical", {"period": "1y"})
            if response and response.get("success"):
                historical_data = response.get("data", {})
                # Create technical analysis chart
                chart = create_technical_analysis_chart(historical_data, {}, self.symbol)
                if chart:
                    st.plotly_chart(chart, use_container_width=True)
    
    def _display_predictions(self):
        """Display price predictions"""
        st.header(f"🔮 {self.symbol} Price Predictions")
        
        st.markdown("""
        <div style="background:#e3f2fd;padding:1rem;border-left:4px solid #1976d2;margin:1rem 0;">
        <strong>📊 Prophet Model Information:</strong><br>
        This prediction uses Facebook's Prophet algorithm, which analyzes historical patterns, 
        trends, and seasonality to forecast future prices. The model includes confidence intervals 
        to show prediction uncertainty.
        </div>
        """, unsafe_allow_html=True)
        
        # Prediction controls
        forecast_days = st.slider("Forecast Days", min_value=7, max_value=90, value=30, step=1)
        
        if st.button("🚀 Generate Prediction", type="primary"):
            with st.spinner(f"Generating {forecast_days}-day prediction for {self.symbol}..."):
                if self.use_api:
                    response = call_api(f"/predictions/{self.symbol}", {"forecast_days": forecast_days})
                    
                    if response and response.get("success"):
                        prediction_data = response.get("data", {})
                        self._display_prediction_results(prediction_data)
                    else:
                        st.error("Unable to generate predictions from API")
                else:
                    st.error("API not available for predictions")
    
    def _display_price_charts(self):
        """Display price and volume charts"""
        if self.use_api:
            response = call_api(f"/stocks/{self.symbol}/historical", {"period": "1y"})
            
            if response and response.get("success"):
                historical_data = response.get("data", {})
                
                # Price chart
                st.subheader("Price Chart")
                price_chart = create_candlestick_chart(historical_data, self.symbol)
                if price_chart:
                    st.plotly_chart(price_chart, use_container_width=True)
                
                # Volume chart
                st.subheader("Volume Chart")
                volume_chart = create_volume_chart(historical_data, self.symbol)
                if volume_chart:
                    st.plotly_chart(volume_chart, use_container_width=True)
        else:
            # Fallback charts using yfinance
            hist_data, _ = get_stock_data_direct(self.symbol, "1y")
            if hist_data is not None and not hist_data.empty:
                st.info("Using fallback data source")
    
    def _display_technical_indicators(self, technical_data: Dict[str, Any]):
        """Display technical indicators summary"""
        if technical_data:
            st.subheader("Current Technical Indicators")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                rsi = technical_data.get('rsi')
                if rsi:
                    st.metric("RSI", f"{rsi:.2f}", technical_data.get('rsi_signal', ''))
            
            with col2:
                current_price = technical_data.get('current_price')
                if current_price:
                    st.metric("Price vs MA20", f"${current_price:.2f}", technical_data.get('ma_signal', ''))
            
            with col3:
                volume = technical_data.get('volume')
                if volume:
                    st.metric("Volume", f"{volume:,.0f}", technical_data.get('volume_signal', ''))
    
    def _display_prediction_results(self, prediction_data: Dict[str, Any]):
        """Display prediction results"""
        current_price = prediction_data.get('current_price', 0)
        predicted_price = prediction_data.get('predicted_price', 0)
        price_change = prediction_data.get('price_change', 0)
        price_change_pct = prediction_data.get('price_change_percent', 0)
        forecast_days = prediction_data.get('forecast_days', 30)
        
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Current Price", f"${current_price:.2f}")
        
        with col2:
            st.metric(
                f"Predicted Price ({forecast_days}d)",
                f"${predicted_price:.2f}",
                f"${price_change:.2f} ({price_change_pct:.2f}%)"
            )
        
        with col3:
            confidence_range = prediction_data.get('confidence_upper', 0) - prediction_data.get('confidence_lower', 0)
            st.metric("Confidence Range", f"±${confidence_range/2:.2f}")
        
        # Prediction chart
        predictions = prediction_data.get('predictions', [])
        if predictions:
            pred_chart = create_prediction_chart(predictions, self.symbol, current_price)
            if pred_chart:
                st.plotly_chart(pred_chart, use_container_width=True)
            
            # Prediction table
            st.subheader("Detailed Predictions")
            pred_df = pd.DataFrame(predictions)
            if not pred_df.empty:
                st.dataframe(pred_df, use_container_width=True)
        
        # Disclaimer
        st.warning("""
        ⚠️ **Investment Disclaimer**: These predictions are for educational purposes only and should not be considered as financial advice. 
        Stock market predictions are inherently uncertain and actual prices may vary significantly from predictions. 
        Always consult with a qualified financial advisor before making investment decisions.
        """)
    
    def _get_fallback_data(self):
        """Get fallback data using yfinance"""
        hist_data, info = get_stock_data_direct(self.symbol, "2d")
        
        if hist_data is not None and not hist_data.empty and len(hist_data) >= 2:
            current_price = float(hist_data['Close'].iloc[-1])
            prev_close = float(hist_data['Close'].iloc[-2])
            price_change = current_price - prev_close
            price_change_pct = (price_change / prev_close) * 100
            
            stock_data = {
                'current_price': current_price,
                'price_change': price_change,
                'price_change_percent': price_change_pct,
                'volume': int(hist_data['Volume'].iloc[-1]),
                'market_cap': info.get('marketCap') if info else None,
                'pe_ratio': info.get('trailingPE') if info else None
            }
            
            company_info = {
                'name': info.get('longName') if info else None,
                'sector': info.get('sector') if info else None,
                'industry': info.get('industry') if info else None,
                'country': info.get('country') if info else None,
                'website': info.get('website') if info else None,
                'employees': info.get('fullTimeEmployees') if info else None
            }
            
            return stock_data, company_info
        
        return None, None