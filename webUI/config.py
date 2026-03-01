# Configuration for the Financial Dashboard Application

# API Configuration
API_HOST = "0.0.0.0"
API_PORT = 8000
API_RELOAD = True

# Frontend Configuration  
FRONTEND_HOST = "localhost"
FRONTEND_PORT = 8501

# Database Configuration (for future use)
DATABASE_URL = "sqlite:///./financial_dashboard.db"

# External API Keys (add your keys here)
ALPHA_VANTAGE_API_KEY = "E4KK7UM0DEJ797ZM"
FINNHUB_API_KEY = "d35tp9pr01qhqkb40140d35tp9pr01qhqkb4014g"
NEWS_API_KEY = "ed8747cf52b849e7aaafa8a3934d29e1"
GEMINI_API_KEY="AIzaSyCMil_XRE20uMZPkT2X5BOKLSUDKgVVXl0"

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FILE = "app.log"

# Cache Configuration
CACHE_TTL_SECONDS = 300  # 5 minutes
ENABLE_CACHING = True

# Security Configuration
SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30