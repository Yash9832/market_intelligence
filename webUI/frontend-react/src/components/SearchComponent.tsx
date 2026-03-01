import React, { useState, useCallback } from 'react';
import {
  Box,
  Typography,
  TextField,
  Paper,
  Alert,
  Chip,
  InputAdornment,
} from '@mui/material';
import {
  Search as SearchIcon,
} from '@mui/icons-material';
import ApiService from '../services/api';
import { debounce } from '../utils/helpers';
import type { SearchResult } from '../types';

interface SearchComponentProps {
  onStockSelect: (symbol: string) => void;
}

const SearchComponent: React.FC<SearchComponentProps> = ({ onStockSelect }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [suggestions, setSuggestions] = useState<SearchResult[]>([]);
  const [apiAvailable, setApiAvailable] = useState(true);
  const [showSuggestions, setShowSuggestions] = useState(false);

  // Popular stocks for quick access
  const popularStocks = [
    { symbol: 'AAPL', name: 'Apple Inc.' },
    { symbol: 'MSFT', name: 'Microsoft Corporation' },
    { symbol: 'GOOGL', name: 'Alphabet Inc.' },
    { symbol: 'TSLA', name: 'Tesla Inc.' },
    { symbol: 'AMZN', name: 'Amazon.com Inc.' },
    { symbol: 'META', name: 'Meta Platforms Inc.' },
    { symbol: 'NVDA', name: 'NVIDIA Corporation' },
    { symbol: 'NFLX', name: 'Netflix Inc.' },
  ];

  // Debounced search function
  const debouncedSearch = useCallback(
    debounce(async (query: string) => {
      if (!query.trim()) {
        setSuggestions([]);
        return;
      }

      try {
        const available = await ApiService.checkHealth();
        setApiAvailable(available);

        if (available) {
          const results = await ApiService.searchStocks(query, 5);
          setSuggestions(results);
        } else {
          // Fallback: filter popular stocks
          const filtered = popularStocks.filter(stock =>
            stock.symbol.toLowerCase().includes(query.toLowerCase()) ||
            stock.name.toLowerCase().includes(query.toLowerCase())
          );
          setSuggestions(filtered);
        }
      } catch (error) {
        console.error('Search error:', error);
        setSuggestions([]);
      }
    }, 300),
    []
  );

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value;
    setSearchQuery(value);
    setShowSuggestions(value.length > 0);
    debouncedSearch(value);
  };

  const handleStockSelect = (symbol: string) => {
    setSearchQuery('');
    setSuggestions([]);
    setShowSuggestions(false);
    onStockSelect(symbol);
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && searchQuery.trim()) {
      handleStockSelect(searchQuery.toUpperCase());
    }
  };

  return (
    <Box sx={{ width: '100%', px: 0 }}>
      {/* Header */}
      <Box sx={{ textAlign: 'center', mb: 6 }}>
        <Typography variant="h4" sx={{ color: 'text.primary', fontWeight: 600, mb: 2 }}>
          Stock Search
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Search for stocks by symbol or company name
        </Typography>
      </Box>

      {/* API Status Alert */}
      {!apiAvailable && (
        <Alert 
          severity="warning" 
          sx={{ 
            mb: 4, 
            bgcolor: 'rgba(255, 152, 0, 0.1)', 
            border: '1px solid rgba(255, 152, 0, 0.3)' 
          }}
        >
          API Backend Offline - Showing sample data
        </Alert>
      )}

      {/* Search Input */}
      <Box sx={{ position: 'relative', mb: 6 }}>
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Search for stocks (e.g., AAPL, Apple, Microsoft...)"
          value={searchQuery}
          onChange={handleSearchChange}
          onKeyPress={handleKeyPress}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
          sx={{
            '& .MuiOutlinedInput-root': {
              bgcolor: 'background.paper',
              '& fieldset': {
                borderColor: 'rgba(255, 255, 255, 0.3)',
              },
              '&:hover fieldset': {
                borderColor: 'rgba(255, 255, 255, 0.5)',
              },
              '&.Mui-focused fieldset': {
                borderColor: 'primary.main',
              },
            },
          }}
        />

        {/* Search Suggestions */}
        {showSuggestions && suggestions.length > 0 && (
          <Paper
            sx={{
              position: 'absolute',
              top: '100%',
              left: 0,
              right: 0,
              zIndex: 10,
              mt: 1,
              maxHeight: 300,
              overflow: 'auto',
              bgcolor: 'background.paper',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              boxShadow: '0px 12px 24px rgba(0,0,0,0.4)'
            }}
          >
            {suggestions.map((suggestion, index) => (
              <Box
                key={`${suggestion.symbol}-${index}`}
                sx={{
                  p: 2,
                  cursor: 'pointer',
                  borderBottom: index < suggestions.length - 1 ? '1px solid rgba(255, 255, 255, 0.1)' : 'none',
                  '&:hover': {
                    bgcolor: 'rgba(255, 255, 255, 0.05)',
                  },
                }}
                onClick={() => handleStockSelect(suggestion.symbol)}
              >
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 2 }}>
                  <Box>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                      {suggestion.symbol}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {suggestion.name.length > 60 ? `${suggestion.name.substring(0, 60)}...` : suggestion.name}
                    </Typography>
                  </Box>
                  <Typography variant="caption" color="text.secondary">
                    Press Enter ↵
                  </Typography>
                </Box>
              </Box>
            ))}
          </Paper>
        )}
      </Box>

      {/* Popular Stocks */}
      <Box>
        <Typography variant="h6" sx={{ mb: 3, color: 'text.secondary' }}>
          Popular Stocks
        </Typography>
        
        <Box sx={{ 
          display: 'grid', 
          gridTemplateColumns: { 
            xs: 'repeat(2, 1fr)', 
            sm: 'repeat(3, 1fr)', 
            md: 'repeat(4, 1fr)', 
            lg: 'repeat(5, 1fr)',
            xl: 'repeat(6, 1fr)'
          }, 
          gap: 2,
          width: '100%'
        }}>
          {popularStocks.map((stock) => (
            <Chip
              key={stock.symbol}
              label={
                <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 0.5 }}>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {stock.symbol}
                  </Typography>
                  <Typography variant="caption" sx={{ opacity: 0.8 }}>
                    {stock.name.length > 15 ? `${stock.name.substring(0, 15)}...` : stock.name}
                  </Typography>
                </Box>
              }
              onClick={() => handleStockSelect(stock.symbol)}
              sx={{
                height: 'auto',
                p: 1.5,
                bgcolor: 'background.paper',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                color: 'text.primary',
                '&:hover': {
                  bgcolor: 'rgba(255, 255, 255, 0.05)',
                  borderColor: 'primary.main',
                },
              }}
            />
          ))}
        </Box>
      </Box>
    </Box>
  );
};

export default SearchComponent;