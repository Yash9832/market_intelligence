import React, { useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Button,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import ApiService from '../services/api';
import { formatCurrency, getPriceChangeColor, getPriceChangeArrow } from '../utils/helpers';
import { useMarketData } from '../contexts/AppStateContext';
import type { MarketIndex, MarketMover } from '../types';

interface MarketOverviewProps {
  onStockSelect: (symbol: string) => void;
}

const MarketOverview: React.FC<MarketOverviewProps> = ({ onStockSelect }) => {
  const {
    marketData,
    setMarketData,
    isDataFresh,
    isLoading,
    setLoading
  } = useMarketData();
  
  const [apiAvailable, setApiAvailable] = React.useState(true);
  const [refreshing, setRefreshing] = React.useState(false);

  const fetchMarketData = async (force: boolean = false) => {
    // Skip fetch if data is fresh and not forcing refresh
    if (!force && isDataFresh()) {
      return;
    }
    
    try {
      setRefreshing(true);
      setLoading(true);
      
      // Check API availability
      const available = await ApiService.checkHealth();
      setApiAvailable(available);

      if (available) {
        // Fetch indices
        const indicesData = await ApiService.getMarketIndices();

        // Fetch market movers
        const gainersData = await ApiService.getMarketMovers('gainers', 'US', 5);
        const losersData = await ApiService.getMarketMovers('losers', 'US', 5);
        
        // Update cached market data
        setMarketData({
          indices: indicesData,
          gainers: gainersData,
          losers: losersData
        });
      } else {
        // Use fallback data
        const fallbackData = {
          indices: [
            { name: 'S&P 500', symbol: '^GSPC', price: 4350.00, change: 15.50, change_percent: 0.36, currency: 'USD' },
            { name: 'NASDAQ', symbol: '^IXIC', price: 13500.00, change: -25.30, change_percent: -0.19, currency: 'USD' },
            { name: 'Dow Jones', symbol: '^DJI', price: 34200.00, change: 125.80, change_percent: 0.37, currency: 'USD' },
          ],
          gainers: [
            { symbol: 'AAPL', name: 'Apple Inc.', price: 175.43, change_percent: 2.34, volume: 45000000 },
            { symbol: 'MSFT', name: 'Microsoft Corp.', price: 338.11, change_percent: 1.87, volume: 32000000 },
            { symbol: 'GOOGL', name: 'Alphabet Inc.', price: 2734.78, change_percent: 1.45, volume: 28000000 },
          ],
          losers: [
            { symbol: 'TSLA', name: 'Tesla Inc.', price: 245.67, change_percent: -2.11, volume: 67000000 },
            { symbol: 'AMZN', name: 'Amazon.com Inc.', price: 3124.56, change_percent: -1.76, volume: 41000000 },
            { symbol: 'META', name: 'Meta Platforms Inc.', price: 312.45, change_percent: -1.23, volume: 35000000 },
          ]
        };
        setMarketData(fallbackData);
      }
      
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch market data:', error);
      setApiAvailable(false);
      setLoading(false);
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchMarketData();
    
    // Set up auto-refresh every 30 seconds if data is old
    const interval = setInterval(() => {
      if (!isDataFresh()) {
        fetchMarketData();
      }
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  // Extract data from cached state
  const indices = marketData.indices || [];
  const gainers = marketData.gainers || [];
  const losers = marketData.losers || [];

  if (isLoading && indices.length === 0) {
    return (
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: 'calc(100vh - 120px)',
        width: '100%'
      }}>
        <CircularProgress size={60} />
      </Box>
    );
  }

  return (
    <Box sx={{ width: '100%', px: 0 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h4" sx={{ color: 'text.primary', fontWeight: 600 }}>
          Market Overview
        </Typography>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={() => fetchMarketData(true)}
          disabled={refreshing}
          sx={{ borderColor: 'rgba(255, 255, 255, 0.3)' }}
        >
          {refreshing ? 'Refreshing...' : 'Refresh'}
        </Button>
      </Box>

      {/* API Status Alert */}
      {!apiAvailable && (
        <Alert severity="warning" sx={{ mb: 4, bgcolor: 'rgba(255, 152, 0, 0.1)', border: '1px solid rgba(255, 152, 0, 0.3)' }}>
          API Backend Offline - Showing sample data
        </Alert>
      )}

      {/* Market Indices */}
      <Box sx={{ mb: 6 }}>
        <Typography variant="h6" sx={{ mb: 3, color: 'text.secondary' }}>
          Major Indices
        </Typography>
        
        <Box sx={{ 
          display: 'grid', 
          gridTemplateColumns: { 
            xs: '1fr', 
            sm: 'repeat(2, 1fr)', 
            md: 'repeat(3, 1fr)', 
            lg: 'repeat(4, 1fr)',
            xl: 'repeat(6, 1fr)'
          }, 
          gap: 3,
          width: '100%'
        }}>
          {indices.map((index) => (
            <Paper
              key={index.symbol}
              sx={{
                p: 3,
                bgcolor: 'background.paper',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: 2,
                minHeight: 140,
              }}
            >
              <Typography variant="body2" sx={{ color: 'text.secondary', mb: 1 }}>
                {index.name}
              </Typography>
              
              <Typography variant="h4" sx={{ mb: 1, color: 'text.primary' }}>
                {formatCurrency(index.price, index.currency)}
              </Typography>
              
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography
                  variant="body2"
                  sx={{ 
                    color: getPriceChangeColor(index.change_percent),
                    display: 'flex',
                    alignItems: 'center',
                    gap: 0.5
                  }}
                >
                  {getPriceChangeArrow(index.change_percent)}
                  {Math.abs(index.change_percent).toFixed(2)}%
                </Typography>
                <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                  ({index.change > 0 ? '+' : ''}{index.change.toFixed(2)})
                </Typography>
              </Box>
            </Paper>
          ))}
        </Box>
      </Box>

      {/* Market Movers */}
      <Box sx={{ 
        display: 'grid', 
        gridTemplateColumns: { xs: '1fr', lg: '1fr 1fr' }, 
        gap: 4,
        width: '100%'
      }}>
        {/* Top Gainers */}
        <Paper sx={{ p: 3, bgcolor: 'background.paper', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <TrendingUp sx={{ color: 'success.main', mr: 1 }} />
            <Typography variant="h6">Top Gainers</Typography>
          </Box>
          
          <Box sx={{ display: 'grid', gap: 2 }}>
            {gainers.slice(0, 5).map((stock) => (
              <Box
                key={stock.symbol}
                sx={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  p: 2,
                  bgcolor: 'rgba(255, 255, 255, 0.02)',
                  borderRadius: 1,
                  cursor: 'pointer',
                  '&:hover': {
                    bgcolor: 'rgba(255, 255, 255, 0.05)',
                  },
                }}
                onClick={() => onStockSelect(stock.symbol)}
              >
                <Box>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {stock.symbol}
                  </Typography>
                  <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                    {stock.name.length > 20 ? `${stock.name.substring(0, 20)}...` : stock.name}
                  </Typography>
                </Box>
                
                <Box sx={{ textAlign: 'right' }}>
                  <Typography variant="body2">
                    ${stock.price.toFixed(2)}
                  </Typography>
                  <Typography
                    variant="body2"
                    sx={{ color: 'success.main' }}
                  >
                    +{stock.change_percent.toFixed(2)}%
                  </Typography>
                </Box>
              </Box>
            ))}
          </Box>
        </Paper>

        {/* Top Losers */}
        <Paper sx={{ p: 3, bgcolor: 'background.paper', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <TrendingDown sx={{ color: 'error.main', mr: 1 }} />
            <Typography variant="h6">Top Losers</Typography>
          </Box>
          
          <Box sx={{ display: 'grid', gap: 2 }}>
            {losers.slice(0, 5).map((stock) => (
              <Box
                key={stock.symbol}
                sx={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  p: 2,
                  bgcolor: 'rgba(255, 255, 255, 0.02)',
                  borderRadius: 1,
                  cursor: 'pointer',
                  '&:hover': {
                    bgcolor: 'rgba(255, 255, 255, 0.05)',
                  },
                }}
                onClick={() => onStockSelect(stock.symbol)}
              >
                <Box>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {stock.symbol}
                  </Typography>
                  <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                    {stock.name.length > 20 ? `${stock.name.substring(0, 20)}...` : stock.name}
                  </Typography>
                </Box>
                
                <Box sx={{ textAlign: 'right' }}>
                  <Typography variant="body2">
                    ${stock.price.toFixed(2)}
                  </Typography>
                  <Typography
                    variant="body2"
                    sx={{ color: 'error.main' }}
                  >
                    {stock.change_percent.toFixed(2)}%
                  </Typography>
                </Box>
              </Box>
            ))}
          </Box>
        </Paper>
      </Box>
    </Box>
  );
};

export default MarketOverview;