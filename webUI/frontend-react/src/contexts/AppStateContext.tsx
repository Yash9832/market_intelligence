import React, { createContext, useContext, useReducer, useEffect } from 'react';
import type { ReactNode } from 'react';

// Types for our global state
export interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  data?: any;
}

export interface MarketData {
  indices?: any[];
  gainers?: any[];
  losers?: any[];
  lastUpdated?: Date;
}

export interface AnalysisData {
  [symbol: string]: {
    data: any;
    timestamp: Date;
  };
}

interface AppState {
  messages: Message[];
  marketData: MarketData;
  analysisData: AnalysisData;
  isLoading: {
    chat: boolean;
    market: boolean;
    analysis: boolean;
  };
}

// Actions for state management
type AppAction = 
  | { type: 'ADD_MESSAGE'; payload: Message }
  | { type: 'SET_MESSAGES'; payload: Message[] }
  | { type: 'CLEAR_MESSAGES' }
  | { type: 'SET_MARKET_DATA'; payload: MarketData }
  | { type: 'SET_ANALYSIS_DATA'; payload: { symbol: string; data: any } }
  | { type: 'SET_LOADING'; payload: { type: keyof AppState['isLoading']; value: boolean } }
  | { type: 'RESTORE_FROM_STORAGE'; payload: Partial<AppState> };

// Initial state
const initialState: AppState = {
  messages: [{
    id: '1',
    type: 'assistant',
    content: '👋 Hi! I\'m your financial assistant. I can help you analyze stocks, get market data, and provide insights. Try asking me about companies like "Tell me about NVIDIA\'s recent performance" or "What\'s Apple\'s current stock price?"',
    timestamp: new Date(),
  }],
  marketData: {},
  analysisData: {},
  isLoading: {
    chat: false,
    market: false,
    analysis: false,
  },
};

// Reducer function
function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case 'ADD_MESSAGE':
      return {
        ...state,
        messages: [...state.messages, action.payload],
      };
    
    case 'SET_MESSAGES':
      return {
        ...state,
        messages: action.payload,
      };
    
    case 'CLEAR_MESSAGES':
      return {
        ...state,
        messages: [initialState.messages[0]], // Keep the welcome message
      };
    
    case 'SET_MARKET_DATA':
      return {
        ...state,
        marketData: {
          ...state.marketData,
          ...action.payload,
          lastUpdated: new Date(),
        },
      };
    
    case 'SET_ANALYSIS_DATA':
      return {
        ...state,
        analysisData: {
          ...state.analysisData,
          [action.payload.symbol]: {
            data: action.payload.data,
            timestamp: new Date(),
          },
        },
      };
    
    case 'SET_LOADING':
      return {
        ...state,
        isLoading: {
          ...state.isLoading,
          [action.payload.type]: action.payload.value,
        },
      };
    
    case 'RESTORE_FROM_STORAGE':
      return {
        ...state,
        ...action.payload,
      };
    
    default:
      return state;
  }
}

// Context
const AppContext = createContext<{
  state: AppState;
  dispatch: React.Dispatch<AppAction>;
} | null>(null);

// Storage keys
const STORAGE_KEYS = {
  MESSAGES: 'financial_dashboard_messages',
  MARKET_DATA: 'financial_dashboard_market_data',
  ANALYSIS_DATA: 'financial_dashboard_analysis_data',
};

// Helper functions for localStorage
const saveToStorage = (key: string, data: any) => {
  try {
    localStorage.setItem(key, JSON.stringify(data));
  } catch (error) {
    console.warn('Failed to save to localStorage:', error);
  }
};

const loadFromStorage = (key: string) => {
  try {
    const data = localStorage.getItem(key);
    return data ? JSON.parse(data) : null;
  } catch (error) {
    console.warn('Failed to load from localStorage:', error);
    return null;
  }
};

// Provider component
export const AppStateProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(appReducer, initialState);

  // Load data from localStorage on mount
  useEffect(() => {
    const savedMessages = loadFromStorage(STORAGE_KEYS.MESSAGES);
    const savedMarketData = loadFromStorage(STORAGE_KEYS.MARKET_DATA);
    const savedAnalysisData = loadFromStorage(STORAGE_KEYS.ANALYSIS_DATA);

    const restoredState: Partial<AppState> = {};

    if (savedMessages && Array.isArray(savedMessages)) {
      // Convert timestamp strings back to Date objects
      const messages = savedMessages.map((msg: any) => ({
        ...msg,
        timestamp: new Date(msg.timestamp),
      }));
      restoredState.messages = messages.length > 0 ? messages : initialState.messages;
    }

    if (savedMarketData) {
      restoredState.marketData = {
        ...savedMarketData,
        lastUpdated: savedMarketData.lastUpdated ? new Date(savedMarketData.lastUpdated) : undefined,
      };
    }

    if (savedAnalysisData) {
      const analysisData: AnalysisData = {};
      Object.keys(savedAnalysisData).forEach(symbol => {
        analysisData[symbol] = {
          ...savedAnalysisData[symbol],
          timestamp: new Date(savedAnalysisData[symbol].timestamp),
        };
      });
      restoredState.analysisData = analysisData;
    }

    if (Object.keys(restoredState).length > 0) {
      dispatch({ type: 'RESTORE_FROM_STORAGE', payload: restoredState });
    }
  }, []);

  // Save data to localStorage whenever state changes
  useEffect(() => {
    saveToStorage(STORAGE_KEYS.MESSAGES, state.messages);
  }, [state.messages]);

  useEffect(() => {
    if (Object.keys(state.marketData).length > 0) {
      saveToStorage(STORAGE_KEYS.MARKET_DATA, state.marketData);
    }
  }, [state.marketData]);

  useEffect(() => {
    if (Object.keys(state.analysisData).length > 0) {
      saveToStorage(STORAGE_KEYS.ANALYSIS_DATA, state.analysisData);
    }
  }, [state.analysisData]);

  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  );
};

// Hook to use the app context
export const useAppState = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppState must be used within AppStateProvider');
  }
  return context;
};

// Helper hooks for specific data types
export const useMessages = () => {
  const { state, dispatch } = useAppState();
  
  const addMessage = (message: Omit<Message, 'id'>) => {
    dispatch({
      type: 'ADD_MESSAGE',
      payload: {
        ...message,
        id: Date.now().toString(),
      },
    });
  };
  
  const clearMessages = () => {
    dispatch({ type: 'CLEAR_MESSAGES' });
  };
  
  return {
    messages: state.messages,
    addMessage,
    clearMessages,
    isLoading: state.isLoading.chat,
    setLoading: (loading: boolean) => dispatch({ type: 'SET_LOADING', payload: { type: 'chat', value: loading } }),
  };
};

export const useMarketData = () => {
  const { state, dispatch } = useAppState();
  
  const setMarketData = (data: MarketData) => {
    dispatch({ type: 'SET_MARKET_DATA', payload: data });
  };
  
  // Check if data is fresh (less than 5 minutes old)
  const isDataFresh = () => {
    if (!state.marketData.lastUpdated) return false;
    const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000);
    return state.marketData.lastUpdated > fiveMinutesAgo;
  };
  
  return {
    marketData: state.marketData,
    setMarketData,
    isDataFresh,
    isLoading: state.isLoading.market,
    setLoading: (loading: boolean) => dispatch({ type: 'SET_LOADING', payload: { type: 'market', value: loading } }),
  };
};

export const useAnalysisData = () => {
  const { state, dispatch } = useAppState();
  
  const setAnalysisData = (symbol: string, data: any) => {
    dispatch({ type: 'SET_ANALYSIS_DATA', payload: { symbol, data } });
  };
  
  const getAnalysisData = (symbol: string) => {
    return state.analysisData[symbol];
  };
  
  // Check if analysis data is fresh (less than 10 minutes old)
  const isAnalysisDataFresh = (symbol: string) => {
    const analysis = state.analysisData[symbol];
    if (!analysis) return false;
    const tenMinutesAgo = new Date(Date.now() - 10 * 60 * 1000);
    return analysis.timestamp > tenMinutesAgo;
  };
  
  return {
    analysisData: state.analysisData,
    setAnalysisData,
    getAnalysisData,
    isAnalysisDataFresh,
    isLoading: state.isLoading.analysis,
    setLoading: (loading: boolean) => dispatch({ type: 'SET_LOADING', payload: { type: 'analysis', value: loading } }),
  };
};