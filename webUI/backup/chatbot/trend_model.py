import re
import yfinance as yf
import pandas as pd
from prophet import Prophet
import matplotlib.pyplot as plt
import io
import base64
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def stock_forecast_tool(ticker: str, periods: int = 7) -> Tuple[str, Optional[str]]:
    """
    Agent-compatible stock prediction tool.
    Input:
        ticker (str): stock ticker symbol
        periods (int): days to predict

    Output:
        tuple:
            text summary (str)
            base64 PNG image as "data:image/png;base64,..." or None on error
    """
    try:
        ticker = ticker.strip().upper()
        if not re.match(r"^[A-Z0-9\.\-]{1,10}$", ticker):
            raise ValueError(f"Invalid ticker '{ticker}'")

        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y", auto_adjust=True)
        if hist.empty:
            raise ValueError(f"No data found for '{ticker}'")

        df = hist[['Close']].reset_index()
        date_col = None
        for col in df.columns:
            if col.lower() in {'date', 'datetime', 'index'} or pd.api.types.is_datetime64_any_dtype(df[col]):
                date_col = col
                break
        if date_col is None:
            raise ValueError("Date column missing from data")

        df = df.rename(columns={date_col: 'ds', 'Close': 'y'})
        df['ds'] = pd.to_datetime(df['ds']).dt.tz_localize(None)

        model = Prophet(daily_seasonality=True)
        model.fit(df[['ds', 'y']])
        future = model.make_future_dataframe(periods=periods, freq='D')
        forecast = model.predict(future)

        recent = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(periods)
        lines = [f"{periods}-day forecast for {ticker}:"]
        for _, row in recent.iterrows():
            date = row['ds'].date()
            lines.append(
                f"Date: {date}, Predicted: {row['yhat']:.2f}, "
                f"Lower: {row['yhat_lower']:.2f}, Upper: {row['yhat_upper']:.2f}"
            )
        summary = "\n".join(lines)

        plt.figure(figsize=(10, 5))
        plt.plot(df['ds'], df['y'], label='Historical', color='blue')
        plt.plot(forecast['ds'], forecast['yhat'], label='Forecast', color='orange')
        plt.fill_between(forecast['ds'], forecast['yhat_lower'], forecast['yhat_upper'], color='orange', alpha=0.3)
        plt.title(f"{ticker} {periods}-Day Forecast")
        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.legend()
        plt.grid(True)

        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()
        image_b64 = base64.b64encode(buf.read()).decode('utf-8')

        # Return data URL string for chatbot-friendly embedding
        image_data = f"data:image/png;base64,{image_b64}"
        return summary, image_data

    except Exception as err:
        logger.error("Forecast tool error", exc_info=True)
        return f"Forecast generation failed: {err}", None


# import yfinance as yf
# import pandas as pd
# from prophet import Prophet
# import logging
# import matplotlib.pyplot as plt
# import time
# from typing import Tuple, Optional

# logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)


# def fetch_stock_data(ticker: str, period: str = "1y", max_retries: int = 3, backoff: float = 1.0) -> pd.DataFrame:
#     """
#     Fetch historical close prices for a valid ticker.
#     Retries on transient errors, and raises clear ValueError if ticker is invalid.
#     """
#     # normalize ticker
#     ticker = ticker.strip().upper()
#     if not re.match(r"^[A-Z0-9\.\-]{1,10}$", ticker):
#         raise ValueError(f"Ticker '{ticker}' contains invalid characters")
    
#     attempt = 0
#     while attempt < max_retries:
#         attempt += 1
#         try:
#             logger.info(f"[{attempt}] Fetching data for {ticker}, period={period}")
#             stock = yf.Ticker(ticker)
#             hist = stock.history(period=period, auto_adjust=True)
#             if hist.empty:
#                 raise ValueError(f"No price data found for ticker '{ticker}'")
#             df = hist[['Close']].reset_index()
#             logger.info(f"Fetched {len(df)} rows for {ticker}")
#             return df
#         except Exception as e:
#             logger.warning(f"Attempt {attempt} failed: {e}")
#             time.sleep(backoff * attempt)
#     # if here, all retries failed
#     raise ConnectionError(f"Failed to fetch data for '{ticker}' after {max_retries} attempts")


# def prepare_data_for_prophet(df: pd.DataFrame) -> pd.DataFrame:
#     """
#     Rename columns and ensure datetime is timezone-naive.
#     """
#     # find date-like column
#     for col in df.columns:
#         if col.lower() in {'date', 'datetime', 'index'} or pd.api.types.is_datetime64_any_dtype(df[col]):
#             df = df.rename(columns={col: 'ds', 'Close': 'y'})
#             df['ds'] = pd.to_datetime(df['ds']).dt.tz_localize(None)
#             logger.info("Prepared DataFrame for Prophet with columns %s", df.columns.tolist())
#             return df[['ds', 'y']]
#     raise ValueError("Input DataFrame lacks a recognizable date column")


# def predict_next_n_days(df_prophet: pd.DataFrame, periods: int = 7) -> Tuple[Prophet, pd.DataFrame]:
#     """
#     Fit a Prophet model and forecast the next `periods` days.
#     """
#     if df_prophet.empty or 'ds' not in df_prophet or 'y' not in df_prophet:
#         raise ValueError("Invalid DataFrame for Prophet: missing 'ds' or 'y'")
#     model = Prophet(daily_seasonality=True)
#     model.fit(df_prophet)
#     future = model.make_future_dataframe(periods=periods, freq='D')
#     forecast = model.predict(future)
#     return model, forecast


# def stock_forecast_tool(ticker: str, periods: int = 7) -> Tuple[str, Optional[str]]:
#     """
#     Wrapper that returns a text summary and a base64-encoded PNG plot.
#     """
#     try:
#         df = fetch_stock_data(ticker)
#         df_prophet = prepare_data_for_prophet(df)
#         model, forecast = predict_next_n_days(df_prophet, periods)
        
#         # Text summary
#         recent = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(periods)
#         text = [f"{periods}-day forecast for {ticker}:"]
#         for _, row in recent.iterrows():
#             date = row['ds'].date()
#             text.append(
#                 f"Date: {date}, Predicted: {row['yhat']:.2f}, "
#                 f"Lower: {row['yhat_lower']:.2f}, Upper: {row['yhat_upper']:.2f}"
#             )
#         summary = "\n".join(text)
        
#         # Plot
#         plt.figure(figsize=(10, 5))
#         plt.plot(df_prophet['ds'], df_prophet['y'], label='Historical', color='blue')
#         plt.plot(forecast['ds'], forecast['yhat'], label='Forecast', color='orange')
#         plt.fill_between(forecast['ds'], forecast['yhat_lower'], forecast['yhat_upper'], color='orange', alpha=0.3)
#         plt.title(f"{ticker} {periods}-Day Forecast")
#         plt.xlabel('Date'); plt.ylabel('Price'); plt.legend(); plt.grid(True)
#         buf = io.BytesIO(); plt.savefig(buf, format='png'); buf.seek(0); plt.close()
#         img_b64 = base64.b64encode(buf.read()).decode('utf-8')
#         return summary, f"data:image/png;base64,{img_b64}"
    
#     except ValueError as ve:
#         return f"Input error: {ve}", None
#     except ConnectionError as ce:
#         return f"Data fetch error: {ce}", None
#     except Exception as e:
#         logger.error("Unexpected error in forecast tool", exc_info=True)
#         return f"Forecast generation failed: {e}", None


# # import yfinance as yf
# # import pandas as pd
# # from prophet import Prophet
# # import logging
# # import matplotlib.pyplot as plt

# # logging.basicConfig(level=logging.INFO)
# # logger = logging.getLogger(__name__)

# # def fetch_stock_data(ticker: str, period: str = "1y") -> pd.DataFrame:
# #     logger.info(f"Fetching historical data for {ticker} for period: {period}")
# #     stock = yf.Ticker(ticker)
# #     hist = stock.history(period=period)
# #     if hist.empty:
# #         raise ValueError(f"No data found for ticker {ticker}")
# #     df = hist[['Close']].reset_index()
# #     logger.info(f"Columns fetched: {df.columns.tolist()}")
# #     return df

# # def prepare_data_for_prophet(df: pd.DataFrame) -> pd.DataFrame:
# #     # Attempt to identify the date-like column for Prophet
# #     date_col = None
# #     for col in df.columns:
# #         if col.lower() in ['date', 'datetime', 'index']:
# #             date_col = col
# #             break
# #     if not date_col:
# #         raise ValueError("No date/datetime column found in dataframe")
# #     df_prophet = df.rename(columns={date_col: 'ds', 'Close': 'y'})
# #     df_prophet['ds'] = pd.to_datetime(df_prophet['ds']).dt.tz_localize(None)
# #     logger.info(f"Prophet DataFrame columns after renaming: {df_prophet.columns.tolist()}")
# #     return df_prophet

# # def predict_next_n_days(df_prophet: pd.DataFrame, periods: int = 7):
# #     model = Prophet(daily_seasonality=True)
# #     model.fit(df_prophet)
# #     future = model.make_future_dataframe(periods=periods)
# #     forecast = model.predict(future)
# #     return model, forecast

# # def plot_forecast(df_prophet: pd.DataFrame, forecast: pd.DataFrame, ticker: str):
# #     plt.figure(figsize=(12, 6))
# #     plt.plot(df_prophet['ds'], df_prophet['y'], label='Historical Close', color='blue')
# #     plt.plot(forecast['ds'], forecast['yhat'], label='Forecast', color='orange')
# #     plt.fill_between(
# #         forecast['ds'],
# #         forecast['yhat_lower'],
# #         forecast['yhat_upper'],
# #         color='orange', alpha=0.3,
# #         label='Confidence Interval'
# #     )
# #     plt.title(f'{ticker} Stock Price Forecast for Next {forecast.shape[0] - df_prophet.shape[0]} Days')
# #     plt.xlabel('Date')
# #     plt.ylabel('Price')
# #     plt.legend()
# #     plt.grid(True)
# #     plt.show()

# # def stock_price_forecast_with_plot(ticker: str, periods: int = 7):
# #     hist_data = fetch_stock_data(ticker)
# #     df_prophet = prepare_data_for_prophet(hist_data)
# #     model, forecast = predict_next_n_days(df_prophet, periods=periods)
# #     print(f"\n{periods}-day forecast for {ticker}:")
# #     print(forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(periods).to_string(index=False))
# #     plot_forecast(df_prophet, forecast, ticker)



# # if __name__ == "__main__":
# #     company_ticker = input("Enter company ticker symbol (e.g. AAPL, MSFT): ").strip().upper()
# #     try:
# #         stock_price_forecast_with_plot(company_ticker)
# #     except Exception as e:
# #         logger.error(f"Failed to predict for ticker {company_ticker}: {e}")