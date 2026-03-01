export interface StockData {
  symbol: string;
  company_name: string;
  current_price: number;
  price_change: number;
  price_change_percent: number;
  volume: number;
  market_cap?: number;
  pe_ratio?: number;
  dividend_yield?: number;
  week_52_high: number;
  week_52_low: number;
  currency: string;
}

export interface CompanyInfo {
  symbol: string;
  name?: string;
  sector?: string;
  industry?: string;
  country?: string;
  website?: string;
  employees?: number;
  description?: string;
  founded?: string;
}

export interface HistoricalData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface TechnicalIndicators {
  rsi: number;
  ma20: number;
  ma50: number;
  signal: string;
}

export interface PredictionData {
  symbol: string;
  forecast_days: number;
  current_price: number;
  predicted_price: number;
  confidence_lower: number;
  confidence_upper: number;
  price_change: number;
  price_change_percent: number;
  predictions: PredictionPoint[];
  day_1: number;
  week_1: number;
  month_1: number;
  confidence?: {
    day_1: number;
    week_1: number;
    month_1: number;
  };
}

export interface PredictionPoint {
  date: string;
  predicted_price: number;
  lower_bound: number;
  upper_bound: number;
}

export interface FinancialMetrics {
  market_cap?: number;
  enterprise_value?: number;
  pe_ratio?: number;
  forward_pe?: number;
  price_to_book?: number;
  gross_margin?: number;
  operating_margin?: number;
  profit_margin?: number;
  roe?: number;
  roa?: number;
  total_cash?: number;
  total_debt?: number;
  debt_to_equity?: number;
  current_ratio?: number;
  quick_ratio?: number;
}

export interface MarketIndex {
  name: string;
  symbol: string;
  price: number;
  change: number;
  change_percent: number;
  currency: string;
}

export interface MarketMover {
  symbol: string;
  name: string;
  price: number;
  change_percent: number;
  volume: number;
}

export interface APIResponse<T = any> {
  success: boolean;
  message: string;
  data?: T;
}

export interface SearchResult {
  symbol: string;
  name: string;
}

export interface NewsItem {
  title: string;
  summary: string;
  time: string;
}