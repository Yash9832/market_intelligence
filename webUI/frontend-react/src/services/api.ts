import axios from 'axios';
import type { 
  APIResponse, 
  StockData, 
  CompanyInfo, 
  HistoricalData, 
  FinancialMetrics, 
  PredictionData, 
  MarketIndex, 
  MarketMover, 
  SearchResult 
} from '../types';

const API_BASE_URL = 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // Increased to 60 seconds for AI processing
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export class ApiService {
  // Health check
  static async checkHealth(): Promise<boolean> {
    try {
      const response = await apiClient.get<APIResponse>('/health');
      return response.data.success;
    } catch {
      return false;
    }
  }

  // Stock search
  static async searchStocks(query: string, limit: number = 10): Promise<SearchResult[]> {
    try {
      const response = await apiClient.get<APIResponse<{ results: SearchResult[] }>>(
        `/stocks/search`,
        { params: { query, limit } }
      );
      return response.data.data?.results || [];
    } catch (error) {
      console.error('Search error:', error);
      return [];
    }
  }

  // Get stock info (split into separate methods)
  static async getStockData(symbol: string): Promise<StockData | null> {
    try {
      const response = await apiClient.get<APIResponse<{
        stock_data: StockData;
        company_info: CompanyInfo;
      }>>(`/stocks/${symbol}/info`);
      
      return response.data.data?.stock_data || null;
    } catch (error) {
      console.error('Stock data error:', error);
      return null;
    }
  }

  // Get company info
  static async getCompanyInfo(symbol: string): Promise<CompanyInfo | null> {
    try {
      const response = await apiClient.get<APIResponse<{
        stock_data: StockData;
        company_info: CompanyInfo;
      }>>(`/stocks/${symbol}/info`);
      
      return response.data.data?.company_info || null;
    } catch (error) {
      console.error('Company info error:', error);
      return null;
    }
  }

  // Get stock info (combined method - keeping for backward compatibility)
  static async getStockInfo(symbol: string): Promise<{
    stock_data: StockData | null;
    company_info: CompanyInfo | null;
  }> {
    try {
      const response = await apiClient.get<APIResponse<{
        stock_data: StockData;
        company_info: CompanyInfo;
      }>>(`/stocks/${symbol}/info`);
      
      return {
        stock_data: response.data.data?.stock_data || null,
        company_info: response.data.data?.company_info || null,
      };
    } catch (error) {
      console.error('Stock info error:', error);
      return { stock_data: null, company_info: null };
    }
  }

  // Get historical data
  static async getHistoricalData(symbol: string, period: string = '1y'): Promise<HistoricalData[]> {
    try {
      const response = await apiClient.get<APIResponse<{
        dates: string[];
        open: number[];
        high: number[];
        low: number[];
        close: number[];
        volume: number[];
      }>>(
        `/stocks/${symbol}/historical`,
        { params: { period } }
      );
      
      if (response.data.data) {
        const { dates, open, high, low, close, volume } = response.data.data;
        return dates.map((date, index) => ({
          date,
          open: open[index],
          high: high[index],
          low: low[index],
          close: close[index],
          volume: volume[index],
        }));
      }
      return [];
    } catch (error) {
      console.error('Historical data error:', error);
      return [];
    }
  }

  // Get financial metrics
  static async getFinancialMetrics(symbol: string): Promise<FinancialMetrics | null> {
    try {
      const response = await apiClient.get<APIResponse<FinancialMetrics>>(
        `/stocks/${symbol}/financials`
      );
      return response.data.data || null;
    } catch (error) {
      console.error('Financial metrics error:', error);
      return null;
    }
  }

  // Get predictions
  static async getPredictions(symbol: string, forecastDays: number = 30): Promise<PredictionData | null> {
    try {
      const response = await apiClient.post<APIResponse<PredictionData>>(
        `/predictions/${symbol}`,
        null,
        { params: { forecast_days: forecastDays } }
      );
      return response.data.data || null;
    } catch (error) {
      console.error('Predictions error:', error);
      return null;
    }
  }

  // Get technical analysis
  static async getTechnicalAnalysis(symbol: string, period: string = '1y'): Promise<any> {
    try {
      const response = await apiClient.get<APIResponse<any>>(
        `/predictions/${symbol}/technical`,
        { params: { period } }
      );
      return response.data.data || null;
    } catch (error) {
      console.error('Technical analysis error:', error);
      return null;
    }
  }

  // Get market indices
  static async getMarketIndices(): Promise<MarketIndex[]> {
    try {
      const response = await apiClient.get<APIResponse<{ indices: MarketIndex[] }>>(
        '/market/indices'
      );
      return response.data.data?.indices || [];
    } catch (error) {
      console.error('Market indices error:', error);
      return [];
    }
  }

  // Get market movers
  static async getMarketMovers(
    category: 'gainers' | 'losers' = 'gainers',
    market: 'US' | 'India' = 'US',
    limit: number = 10
  ): Promise<MarketMover[]> {
    try {
      const response = await apiClient.get<APIResponse<{ movers: MarketMover[] }>>(
        '/market/movers',
        { params: { category, market, limit } }
      );
      return response.data.data?.movers || [];
    } catch (error) {
      console.error('Market movers error:', error);
      return [];
    }
  }

  // Get predictions
  static async getPrediction(symbol: string, days: number = 7): Promise<PredictionData | null> {
    try {
      const response = await apiClient.post<APIResponse<PredictionData>>(
        `/predictions/${symbol}`,
        null,
        { 
          params: { forecast_days: days },
          timeout: 120000 // 2 minutes timeout for predictions
        }
      );
      return response.data.data || null;
    } catch (error) {
      console.error('Prediction error:', error);
      return null;
    }
  }

  // Chatbot methods
  static async sendChatMessage(message: string, conversationHistory: Array<{role: string, content: string}> = []): Promise<any> {
    try {
      const response = await apiClient.post<APIResponse>('/chatbot/chat', {
        message,
        conversation_history: conversationHistory
      });
      return response.data;
    } catch (error) {
      console.error('Chat error:', error);
      throw error;
    }
  }

  static async extractEntities(text: string): Promise<any> {
    try {
      const response = await apiClient.post<APIResponse>('/chatbot/extract-entities', {
        text
      });
      return response.data;
    } catch (error) {
      console.error('Entity extraction error:', error);
      throw error;
    }
  }
}

export default ApiService;