import yfinance as yf
import pandas as pd
import numpy as np
import json


def universal_converter(obj):
    import datetime

    if isinstance(obj, dict):
        return {str(k): universal_converter(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [universal_converter(i) for i in obj]
    elif isinstance(obj, (np.integer, np.int64, int)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, float)):
        return float(obj)
    elif pd.isna(obj):
        return None
    elif isinstance(obj, (datetime.date, datetime.datetime, pd.Timestamp)):
        return obj.isoformat()
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj


def df_to_serializable_dict(df):
    if df is None or df.empty:
        return {}
    df = df.copy()
    df.index = df.index.map(str)
    dict_data = df.to_dict(orient='index')
    return universal_converter(dict_data)


def filter_key_fields(df, key_fields):
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.copy()
    df.index = df.index.map(str)
    filtered_df = df.loc[df.index.intersection(key_fields)]
    return filtered_df


def calculate_ratios(income_dict, balance_dict):
    ratios = {}
    try:
        revenue = None
        operating_income = None
        net_income = None
        total_liab = None
        total_equity = None

        # income_dict and balance_dict are dicts of dicts, pick the most recent year (first key)
        if income_dict:
            first_key = next(iter(income_dict))
            revenue = income_dict[first_key].get("Total Revenue")
            operating_income = income_dict[first_key].get("Operating Income")
            net_income = income_dict[first_key].get("Net Income")

        if balance_dict:
            first_key = next(iter(balance_dict))
            total_liab = balance_dict[first_key].get("Total Liab")
            total_equity = balance_dict[first_key].get("Total Stockholder Equity")

        if revenue and operating_income:
            ratios["Operating Margin"] = operating_income / revenue
        if revenue and net_income:
            ratios["Net Profit Margin"] = net_income / revenue
        if total_liab and total_equity and total_equity != 0:
            ratios["Debt to Equity"] = total_liab / total_equity
    except Exception:
        pass

    return {k: float(v) if v is not None else None for k, v in ratios.items()}


def get_clean_data(symbol: str):
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="1d")
    current_price = hist['Close'].iloc[-1] if not hist.empty else None
    current_volume = hist['Volume'].iloc[-1] if not hist.empty else None

    info = ticker.info
    summary = {
        "Symbol": symbol,
        "Current Price": current_price,
        "Current Volume": current_volume,
        "Market Cap": info.get("marketCap"),
        "PE Ratio (Trailing)": info.get("trailingPE"),
        "PE Ratio (Forward)": info.get("forwardPE"),
        "Sector": info.get("sector"),
        "Industry": info.get("industry"),
        "Dividend Yield": info.get("dividendYield"),
        "52 Week High": info.get("fiftyTwoWeekHigh"),
        "52 Week Low": info.get("fiftyTwoWeekLow"),
        "EPS (TTM)": info.get("trailingEps"),
    }
    summary = universal_converter(summary)

    # Define key fields to keep
    income_keys = ["Total Revenue", "Gross Profit", "Operating Income", "Net Income", "Earnings Per Share"]
    balance_keys = [
        "Total Assets", "Total Liab", "Total Stockholder Equity",
        "Current Assets", "Current Liabilities", "Cash And Cash Equivalents", "Long Term Debt"
    ]
    cashflow_keys = [
        "Operating Cash Flow", "Capital Expenditure", "Free Cash Flow",
        "Investing Cash Flow", "Financing Cash Flow", "Change In Cash And Cash Equivalents"
    ]

    filtered_income = filter_key_fields(ticker.financials, income_keys)
    filtered_balance = filter_key_fields(ticker.balance_sheet, balance_keys)
    filtered_cashflow = filter_key_fields(ticker.cashflow, cashflow_keys)

    income_stmt = df_to_serializable_dict(filtered_income)
    balance_sheet = df_to_serializable_dict(filtered_balance)
    cashflow = df_to_serializable_dict(filtered_cashflow)

    ratios = calculate_ratios(income_stmt, balance_sheet)

    result = {
        "summary": summary,
        "income_statement": income_stmt,
        "balance_sheet": balance_sheet,
        "cash_flow": cashflow,
        "derived_ratios": ratios
    }

    return universal_converter(result)


if __name__ == "__main__":
    data = get_clean_data("AAPL")
    with open('stock_data.json', 'w') as f:
        json.dump(data, f, indent=4)
    print("Data saved to stock_data.json")