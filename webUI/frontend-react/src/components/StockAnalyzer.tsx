import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  TextField,
  Button,
  Chip,
  Skeleton,
  Divider,
  LinearProgress,
} from '@mui/material';
import {
  TrendingUp,
  Analytics,
  Timeline,
  Search as SearchIcon,
  AccountBalance,
} from '@mui/icons-material';
import ApiService from '../services/api';
import { formatCurrency, formatNumber, getPriceChangeColor, getPriceChangeArrow } from '../utils/helpers';
import VolumeChart from './VolumeChart';
import PriceChart from './PriceChart';
import { TechnicalAnalysisChart } from './TechnicalAnalysisChart';
import { PredictionChart } from './PredictionChart';
import ErrorBoundary from './ErrorBoundary';
import SectionHeader from './common/SectionHeader';
import LiveNewsFeed from './LiveNewsFeed';
import type { StockData, CompanyInfo, HistoricalData, FinancialMetrics, PredictionData } from '../types';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`analyzer-tabpanel-${index}`}
      aria-labelledby={`analyzer-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

interface StockAnalyzerProps {
  selectedSymbol: string | null;
  onSymbolChange: (symbol: string) => void;
}

const StockAnalyzer: React.FC<StockAnalyzerProps> = ({ selectedSymbol, onSymbolChange }) => {
  const [tabValue, setTabValue] = useState(0);
  const [stockData, setStockData] = useState<StockData | null>(null);
  const [companyInfo, setCompanyInfo] = useState<CompanyInfo | null>(null);
  const [historicalData, setHistoricalData] = useState<HistoricalData[]>([]);
  const [financialMetrics, setFinancialMetrics] = useState<FinancialMetrics | null>(null);
  const [loading, setLoading] = useState(false);
  const [apiAvailable, setApiAvailable] = useState(true);
  const [searchSymbol, setSearchSymbol] = useState('');
  const [technicalAnalysis, setTechnicalAnalysis] = useState<any>(null);
  const [predictions, setPredictions] = useState<PredictionData | null>(null);
  const [loadingPredictions, setLoadingPredictions] = useState(false);

  const fetchStockData = async (symbol: string) => {
    if (!symbol) return;
    
    try {
      setLoading(true);
      
      // Check API availability
      const available = await ApiService.checkHealth();
      setApiAvailable(available);

      if (available) {
        // Fetch all stock data
        const [stockInfo, compInfo, histData, finMetrics, techAnalysis] = await Promise.allSettled([
          ApiService.getStockData(symbol),
          ApiService.getCompanyInfo(symbol),
          ApiService.getHistoricalData(symbol, '6mo'),
          ApiService.getFinancialMetrics(symbol),
          ApiService.getTechnicalAnalysis(symbol)
        ]);

        if (stockInfo.status === 'fulfilled' && stockInfo.value) {
          setStockData(stockInfo.value);
        }
        if (compInfo.status === 'fulfilled' && compInfo.value) {
          setCompanyInfo(compInfo.value);
        }
        if (histData.status === 'fulfilled' && histData.value) {
          setHistoricalData(histData.value);
        }
        if (finMetrics.status === 'fulfilled' && finMetrics.value) {
          setFinancialMetrics(finMetrics.value);
        }
        if (techAnalysis.status === 'fulfilled' && techAnalysis.value) {
          setTechnicalAnalysis(techAnalysis.value);
        }
      } else {
        // Use fallback data
        const generateMockHistoricalData = (): HistoricalData[] => {
          const data: HistoricalData[] = [];
          const baseVolume = 45000000;
          for (let i = 29; i >= 0; i--) {
            const date = new Date();
            date.setDate(date.getDate() - i);
            data.push({
              date: date.toISOString().split('T')[0],
              open: 148 + Math.random() * 4,
              high: 150 + Math.random() * 5,
              low: 145 + Math.random() * 3,
              close: 149 + Math.random() * 3,
              volume: Math.floor(baseVolume * (0.7 + Math.random() * 0.6))
            });
          }
          return data;
        };

        setHistoricalData(generateMockHistoricalData());
        
        setFinancialMetrics({
          market_cap: 3640000000000,
          enterprise_value: 3690000000000,
          pe_ratio: 37.31003,
          forward_pe: 29.542719,
          price_to_book: 55.405098,
          gross_margin: 0.4668,
          operating_margin: 0.2999,
          profit_margin: 0.2430,
          roe: 1.4981,
          roa: 0.2455,
          total_cash: 55370000000,
          total_debt: 101700000000,
          debt_to_equity: 154.486,
          current_ratio: 0.868,
          quick_ratio: 0.724,
        });
        
        setStockData({
          symbol: symbol.toUpperCase(),
          company_name: `${symbol.toUpperCase()} Company`,
          current_price: 150.00,
          price_change: 2.50,
          price_change_percent: 1.69,
          volume: 45000000,
          market_cap: 2500000000000,
          pe_ratio: 25.4,
          dividend_yield: 0.65,
          week_52_high: 180.00,
          week_52_low: 120.00,
          currency: 'USD',
        });
        
        setCompanyInfo({
          symbol: symbol.toUpperCase(),
          name: `${symbol.toUpperCase()} Company`,
          sector: 'Technology',
          industry: 'Software',
          employees: 150000,
          description: `${symbol.toUpperCase()} is a leading technology company focused on innovative software solutions.`,
          founded: '1976',
        });
      }
      
    } catch (error) {
      console.error('Failed to fetch stock data:', error);
      setApiAvailable(false);
    } finally {
      setLoading(false);
    }
  };

  const fetchPredictions = async (days: number) => {
    if (!selectedSymbol) return;
    
    setLoadingPredictions(true);
    
    // Create a timeout promise
    const timeoutPromise = new Promise((_, reject) => {
      setTimeout(() => reject(new Error('Request timed out after 2 minutes')), 120000);
    });
    
    try {
      console.log(`Fetching predictions for ${selectedSymbol} with ${days} days...`);
      
      // Race between the actual API call and timeout
      const predictionData = await Promise.race([
        ApiService.getPrediction(selectedSymbol, days),
        timeoutPromise
      ]) as PredictionData | null;
      
      if (predictionData) {
        console.log('Prediction data received:', predictionData);
        setPredictions(predictionData);
      } else {
        console.log('No prediction data received, using fallback');
        throw new Error('No prediction data received from API');
      }
    } catch (error) {
      console.error('Failed to fetch predictions:', error);
      // Always provide fallback data on error to prevent UI issues
      const today = new Date();
      const fallbackData: PredictionData = {
        symbol: selectedSymbol.toUpperCase(),
        forecast_days: days,
        current_price: 150.00,
        predicted_price: 155.00,
        confidence_lower: 150.00,
        confidence_upper: 160.00,
        price_change: 5.00,
        price_change_percent: 3.33,
        predictions: Array.from({ length: days }, (_, i) => {
          const futureDate = new Date(today);
          futureDate.setDate(today.getDate() + i + 1);
          return {
            date: futureDate.toISOString().split('T')[0],
            predicted_price: 150 + Math.random() * 10 - 5,
            lower_bound: 145 + Math.random() * 5,
            upper_bound: 155 + Math.random() * 5
          };
        }),
        day_1: 151.00,
        week_1: 153.00,
        month_1: 158.00,
        confidence: {
          day_1: 0.85,
          week_1: 0.75,
          month_1: 0.65
        }
      };
      setPredictions(fallbackData);
    } finally {
      setLoadingPredictions(false);
    }
  };

  useEffect(() => {
    if (selectedSymbol) {
      fetchStockData(selectedSymbol);
    }
  }, [selectedSymbol]);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleSymbolSearch = () => {
    if (searchSymbol.trim()) {
      onSymbolChange(searchSymbol.toUpperCase());
      setSearchSymbol('');
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter') {
      handleSymbolSearch();
    }
  };

  if (!selectedSymbol) {
    return (
      <Box sx={{ width: '100%', px: 0 }}>
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Analytics sx={{ fontSize: 64, color: 'text.secondary', mb: 3 }} />
          <Typography variant="h4" sx={{ mb: 2, color: 'text.primary' }}>
            Stock Analysis
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
            Enter a stock symbol to begin detailed analysis
          </Typography>
          
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', maxWidth: 400, mx: 'auto' }}>
            <TextField
              label="Stock Symbol"
              variant="outlined"
              value={searchSymbol}
              onChange={(e) => setSearchSymbol(e.target.value.toUpperCase())}
              onKeyPress={handleKeyPress}
              placeholder="e.g., GOOGL"
              sx={{ flex: 1 }}
            />
            <Button
              variant="contained"
              size="large"
              onClick={handleSymbolSearch}
              disabled={!searchSymbol.trim()}
              startIcon={<SearchIcon />}
            >
              Analyze
            </Button>
          </Box>
        </Box>
      </Box>
    );
  }

  return (
    <Box sx={{ width: '100%', px: 0 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <SectionHeader
          title="Stock Analysis"
          subtitle={stockData ? stockData.symbol : undefined}
        />
      </Box>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 0 }}>
        <Tabs 
          value={tabValue} 
          onChange={handleTabChange} 
          aria-label="stock analyzer tabs"
        >
          <Tab icon={<TrendingUp />} label="Overview" />
          <Tab icon={<AccountBalance />} label="Financials" />
          <Tab icon={<Analytics />} label="Analysis" />
          <Tab icon={<Timeline />} label="Prediction" />
        </Tabs>
      </Box>

      {loading && (
        <Box sx={{ py: 2 }}>
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1.5fr 1fr' }, gap: 2 }}>
            <Paper sx={{ p: 3 }}>
              <Skeleton variant="text" width={160} height={36} />
              <Skeleton variant="text" width={120} height={28} />
              <Skeleton variant="rectangular" height={120} sx={{ mt: 2, borderRadius: 1 }} />
            </Paper>
            <Paper sx={{ p: 3 }}>
              <Skeleton variant="text" width={120} />
              {[...Array(6)].map((_, i) => (
                <Skeleton key={i} variant="text" width={220} />
              ))}
            </Paper>
          </Box>
        </Box>
      )}

      {/* Tab Panels */}
      <TabPanel value={tabValue} index={0}>
        {!apiAvailable && (
          <Alert 
            severity="warning" 
            sx={{ 
              mb: 3, 
              bgcolor: 'rgba(255, 152, 0, 0.1)', 
              border: '1px solid rgba(255, 152, 0, 0.3)' 
            }}
          >
            API Backend Offline - Showing sample data
          </Alert>
        )}

        {stockData && (
          <Box sx={{ display: 'grid', gap: 4 }}>
            {/* Price Header */}
            <Paper sx={{ p: 3, border: '1px solid rgba(255, 255, 255, 0.1)' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
                <Box>
                  <Typography variant="overline" sx={{ color: 'text.secondary' }}>Current Price</Typography>
                  <Typography variant="h3" sx={{ color: 'text.primary', lineHeight: 1 }}>
                    {formatCurrency(stockData.current_price, stockData.currency)}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Chip
                    label={`${getPriceChangeArrow(stockData.price_change_percent)} ${Math.abs(stockData.price_change_percent).toFixed(2)}%`}
                    color={stockData.price_change_percent >= 0 ? 'success' : 'error'}
                    variant="outlined"
                  />
                  <Chip
                    label={`${getPriceChangeArrow(stockData.price_change)} ${formatCurrency(Math.abs(stockData.price_change), stockData.currency)} today`}
                    variant="outlined"
                  />
                </Box>
              </Box>
            </Paper>

            {/* Key Stats Grid */}
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 4 }}>
              {/* Key Statistics */}
              <Paper sx={{ p: 3, border: '1px solid rgba(255, 255, 255, 0.1)' }}>
                <Typography variant="h6" sx={{ mb: 2 }}>Key Statistics</Typography>
                <Divider sx={{ mb: 2, borderColor: 'rgba(255,255,255,0.08)' }} />
                <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr 1fr', sm: 'repeat(3, 1fr)' }, gap: 2 }}>
                  {[
                    { label: 'Market Cap', value: formatNumber(stockData.market_cap || 0) },
                    { label: 'Volume', value: formatNumber(stockData.volume) },
                    { label: 'P/E Ratio', value: stockData.pe_ratio?.toFixed(2) || 'N/A' },
                    { label: 'Dividend Yield', value: `${stockData.dividend_yield?.toFixed(2) || '0.00'}%` },
                    { label: '52W Low', value: stockData.week_52_low ? formatCurrency(stockData.week_52_low, stockData.currency) : 'N/A' },
                    { label: '52W High', value: stockData.week_52_high ? formatCurrency(stockData.week_52_high, stockData.currency) : 'N/A' },
                  ].map((stat, index) => (
                    <Paper key={index} sx={{ p: 2, bgcolor: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)' }}>
                      <Typography variant="caption" color="text.secondary">{stat.label}</Typography>
                      <Typography variant="body1" sx={{ mt: 0.5, fontWeight: 600 }}>{stat.value}</Typography>
                    </Paper>
                  ))}
                </Box>
              </Paper>

              {/* 52-Week Range */}
              <Paper sx={{ p: 3, border: '1px solid rgba(255, 255, 255, 0.1)' }}>
                <Typography variant="h6" sx={{ mb: 3 }}>52-Week Range</Typography>
                <Box sx={{ mb: 3 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">Low</Typography>
                    <Typography variant="body2" color="text.secondary">High</Typography>
                  </Box>
                  
                  <Box sx={{
                    height: 8,
                    bgcolor: 'rgba(255, 255, 255, 0.1)',
                    borderRadius: 4,
                    position: 'relative',
                    mb: 2,
                  }}>
                    {stockData.week_52_high && stockData.week_52_low && (
                      <Box sx={{
                        position: 'absolute',
                        left: `${Math.min(Math.max(((stockData.current_price - stockData.week_52_low) / (stockData.week_52_high - stockData.week_52_low)) * 100, 5), 95)}%`,
                        top: -6,
                        width: 20,
                        height: 20,
                        bgcolor: 'primary.main',
                        borderRadius: '50%',
                        border: '2px solid',
                        borderColor: 'background.paper',
                        transform: 'translateX(-50%)',
                      }} />
                    )}
                  </Box>
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography fontWeight="medium">
                      {stockData.week_52_low ? formatCurrency(stockData.week_52_low, stockData.currency) : 'N/A'}
                    </Typography>
                    <Typography fontWeight="medium">
                      {stockData.week_52_high ? formatCurrency(stockData.week_52_high, stockData.currency) : 'N/A'}
                    </Typography>
                  </Box>
                </Box>
              </Paper>
            </Box>

            {/* Company Info */}
            {companyInfo && (
              <Paper sx={{ p: 3, bgcolor: 'background.paper', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
                <Typography variant="h6" sx={{ mb: 3 }}>Company Information</Typography>
                <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3 }}>
                  <Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      Sector
                    </Typography>
                    <Typography variant="body1" sx={{ mb: 2 }}>
                      {companyInfo.sector || 'Technology'}
                    </Typography>
                    
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      Industry
                    </Typography>
                    <Typography variant="body1">
                      {companyInfo.industry || 'Software'}
                    </Typography>
                  </Box>
                  
                  <Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      Employees
                    </Typography>
                    <Typography variant="body1" sx={{ mb: 2 }}>
                      {formatNumber(companyInfo.employees || 150000)}
                    </Typography>
                    
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      Founded
                    </Typography>
                    <Typography variant="body1">
                      {companyInfo.founded || '1976'}
                    </Typography>
                  </Box>
                </Box>
                
                {companyInfo.description && (
                  <Box sx={{ mt: 3 }}>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      About
                    </Typography>
                    <Typography variant="body2" sx={{ lineHeight: 1.6 }}>
                      {companyInfo.description}
                    </Typography>
                  </Box>
                )}
              </Paper>
            )}

            {/* Price Chart */}
            {historicalData.length > 0 && (
              <Paper sx={{ p: 3, border: '1px solid rgba(255, 255, 255, 0.1)' }}>
                <PriceChart data={historicalData} title="Stock Price (Last 60 Days)" symbol={stockData?.symbol} />
              </Paper>
            )}

            {/* Volume Chart */}
            {historicalData.length > 0 && (
              <Paper sx={{ p: 3, border: '1px solid rgba(255, 255, 255, 0.1)' }}>
                <VolumeChart data={historicalData} title="Volume (Last 30 Days)" />
              </Paper>
            )}
          </Box>
        )}
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        {!apiAvailable && (
          <Alert 
            severity="warning" 
            sx={{ 
              mb: 3, 
              bgcolor: 'rgba(255, 152, 0, 0.1)', 
              border: '1px solid rgba(255, 152, 0, 0.3)' 
            }}
          >
            API Backend Offline - Showing sample data
          </Alert>
        )}

        {financialMetrics && (
          <Box sx={{ display: 'grid', gap: 4 }}>
            {/* KPI Row */}
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5 }}>
              <Chip label={`Market Cap: ${financialMetrics.market_cap ? `$${(financialMetrics.market_cap / 1e12).toFixed(2)}T` : 'N/A'}`} variant="outlined" />
              <Chip label={`P/E: ${financialMetrics.pe_ratio ? financialMetrics.pe_ratio.toFixed(2) : 'N/A'}`} variant="outlined" />
              <Chip label={`D/E: ${financialMetrics.debt_to_equity ? financialMetrics.debt_to_equity.toFixed(2) : 'N/A'}`} variant="outlined" />
              <Chip label={`Cash: ${financialMetrics.total_cash ? `$${(financialMetrics.total_cash / 1e9).toFixed(1)}B` : 'N/A'}`} variant="outlined" />
              <Chip label={`Debt: ${financialMetrics.total_debt ? `$${(financialMetrics.total_debt / 1e9).toFixed(1)}B` : 'N/A'}`} variant="outlined" />
            </Box>
            {/* Valuation Metrics */}
            <Paper sx={{ p: 3, border: '1px solid rgba(255, 255, 255, 0.1)' }}>
              <Typography variant="h6" sx={{ mb: 1.5 }}>Valuation</Typography>
              <Divider sx={{ mb: 2, borderColor: 'rgba(255,255,255,0.08)' }} />
              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr 1fr', md: 'repeat(3, 1fr)' }, gap: 2 }}>
                {[ 
                  { label: 'Market Cap', value: financialMetrics.market_cap ? `$${(financialMetrics.market_cap / 1e12).toFixed(2)}T` : 'N/A' },
                  { label: 'Enterprise Value', value: financialMetrics.enterprise_value ? `$${(financialMetrics.enterprise_value / 1e12).toFixed(2)}T` : 'N/A' },
                  { label: 'P/E Ratio', value: financialMetrics.pe_ratio ? financialMetrics.pe_ratio.toFixed(2) : 'N/A' },
                  { label: 'Forward P/E', value: financialMetrics.forward_pe ? financialMetrics.forward_pe.toFixed(2) : 'N/A' },
                  { label: 'Price/Book', value: financialMetrics.price_to_book ? financialMetrics.price_to_book.toFixed(2) : 'N/A' },
                ].map((m, i) => (
                  <Paper key={i} sx={{ p: 2, bgcolor: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)' }}>
                    <Typography variant="caption" color="text.secondary">{m.label}</Typography>
                    <Typography variant="body1" sx={{ mt: 0.5, fontWeight: 600 }}>{m.value}</Typography>
                  </Paper>
                ))}
              </Box>
            </Paper>

            {/* Profitability */}
            <Paper sx={{ p: 3, border: '1px solid rgba(255, 255, 255, 0.1)' }}>
              <Typography variant="h6" sx={{ mb: 1.5 }}>Profitability</Typography>
              <Divider sx={{ mb: 2, borderColor: 'rgba(255,255,255,0.08)' }} />
              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 2 }}>
                {[
                  { label: 'Gross Margin', value: financialMetrics.gross_margin },
                  { label: 'Operating Margin', value: financialMetrics.operating_margin },
                  { label: 'Profit Margin', value: financialMetrics.profit_margin },
                  { label: 'ROE', value: financialMetrics.roe },
                  { label: 'ROA', value: financialMetrics.roa },
                ].map((m, i) => (
                  <Paper key={i} sx={{ p: 2, bgcolor: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)' }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="caption" color="text.secondary">{m.label}</Typography>
                      <Typography variant="caption" color="text.secondary">{m.value !== null && m.value !== undefined ? `${(m.value * 100).toFixed(1)}%` : 'N/A'}</Typography>
                    </Box>
                    <LinearProgress variant="determinate" value={m.value !== null && m.value !== undefined ? Math.max(0, Math.min(100, m.value * 100)) : 0} sx={{ height: 8, borderRadius: 999 }} />
                  </Paper>
                ))}
              </Box>
            </Paper>

            {/* Financial Health */}
            <Paper sx={{ p: 3, border: '1px solid rgba(255, 255, 255, 0.1)' }}>
              <Typography variant="h6" sx={{ mb: 1.5 }}>Financial Health</Typography>
              <Divider sx={{ mb: 2, borderColor: 'rgba(255,255,255,0.08)' }} />
              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, gap: 2 }}>
                {[
                  { label: 'Total Cash', value: financialMetrics.total_cash ? `$${(financialMetrics.total_cash / 1e9).toFixed(1)}B` : 'N/A' },
                  { label: 'Total Debt', value: financialMetrics.total_debt ? `$${(financialMetrics.total_debt / 1e9).toFixed(1)}B` : 'N/A' },
                  { label: 'Debt/Equity', value: financialMetrics.debt_to_equity ? financialMetrics.debt_to_equity.toFixed(2) : 'N/A' },
                  { label: 'Current Ratio', value: financialMetrics.current_ratio ? financialMetrics.current_ratio.toFixed(3) : 'N/A' },
                  { label: 'Quick Ratio', value: financialMetrics.quick_ratio ? financialMetrics.quick_ratio.toFixed(3) : 'N/A' },
                ].map((m, i) => (
                  <Paper key={i} sx={{ p: 2, bgcolor: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)' }}>
                    <Typography variant="caption" color="text.secondary">{m.label}</Typography>
                    <Typography variant="body1" sx={{ mt: 0.5, fontWeight: 600 }}>{m.value}</Typography>
                  </Paper>
                ))}
              </Box>
            </Paper>
          </Box>
        )}
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: '2fr 1fr' }, gap: 2 }}>
          <Box>
            {historicalData.length > 0 ? (
              <TechnicalAnalysisChart 
                data={historicalData} 
                technicalAnalysis={technicalAnalysis}
              />
            ) : (
              <Paper sx={{ p: 6, textAlign: 'center', bgcolor: 'background.paper', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
                <Analytics sx={{ fontSize: 64, color: 'text.secondary', mb: 3 }} />
                <Typography variant="h6" sx={{ mb: 2 }}>Technical Analysis</Typography>
                <Typography color="text.secondary">
                  Search for a stock to view technical analysis
                </Typography>
              </Paper>
            )}
          </Box>
          <Box>
            <LiveNewsFeed symbol={selectedSymbol} companyName={stockData?.company_name || companyInfo?.name || null} />
          </Box>
        </Box>
      </TabPanel>

      <TabPanel value={tabValue} index={3}>
        <ErrorBoundary>
          <PredictionChart
            symbol={selectedSymbol}
            historicalData={historicalData}
            predictions={predictions}
            onFetchPredictions={fetchPredictions}
            loading={loadingPredictions}
          />
        </ErrorBoundary>
      </TabPanel>
    </Box>
  );
};

export default StockAnalyzer;