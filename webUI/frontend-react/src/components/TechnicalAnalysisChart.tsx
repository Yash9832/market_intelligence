import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import type { ChartOptions } from 'chart.js';
import { Line } from 'react-chartjs-2';
import { Box, Typography, Card, CardContent } from '@mui/material';
import type { HistoricalData } from '../types';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface TechnicalAnalysisChartProps {
  data: HistoricalData[];
  technicalAnalysis?: any;
}

export const TechnicalAnalysisChart: React.FC<TechnicalAnalysisChartProps> = ({ 
  data, 
  technicalAnalysis 
}) => {
  if (!data || data.length === 0) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="h6" color="text.secondary">
          No technical analysis data available
        </Typography>
      </Box>
    );
  }

  // Calculate moving averages
  const calculateMA = (prices: number[], period: number) => {
    const ma = [];
    for (let i = 0; i < prices.length; i++) {
      if (i < period - 1) {
        ma.push(null);
      } else {
        const sum = prices.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0);
        ma.push(sum / period);
      }
    }
    return ma;
  };

  // Calculate RSI
  const calculateRSI = (prices: number[], period = 14) => {
    if (prices.length < period + 1) return Array(prices.length).fill(null);
    
    const rsi = [];
    const gains = [];
    const losses = [];
    
    // Calculate price changes
    for (let i = 1; i < prices.length; i++) {
      const change = prices[i] - prices[i - 1];
      gains.push(change > 0 ? change : 0);
      losses.push(change < 0 ? Math.abs(change) : 0);
    }
    
    // Calculate RSI
    for (let i = 0; i < gains.length; i++) {
      if (i < period - 1) {
        rsi.push(null);
      } else {
        const avgGain = gains.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0) / period;
        const avgLoss = losses.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0) / period;
        const rs = avgGain / (avgLoss || 0.01);
        rsi.push(100 - (100 / (1 + rs)));
      }
    }
    
    return [null, ...rsi]; // Add null for first price (no change)
  };

  const prices = data.map(d => d.close);
  const dates = data.map(d => d.date);
  const ma20 = calculateMA(prices, 20);
  const ma50 = calculateMA(prices, 50);
  const rsi = calculateRSI(prices);

  const priceChartData = {
    labels: dates,
    datasets: [
      {
        label: 'Price',
        data: prices,
        borderColor: '#2196F3',
        backgroundColor: 'rgba(33, 150, 243, 0.1)',
        borderWidth: 2,
        pointRadius: 0,
        tension: 0.1,
      },
      {
        label: 'MA20',
        data: ma20,
        borderColor: '#FF9800',
        backgroundColor: 'transparent',
        borderWidth: 1,
        pointRadius: 0,
        tension: 0.1,
      },
      {
        label: 'MA50',
        data: ma50,
        borderColor: '#4CAF50',
        backgroundColor: 'transparent',
        borderWidth: 1,
        pointRadius: 0,
        tension: 0.1,
      },
    ],
  };

  const rsiChartData = {
    labels: dates,
    datasets: [
      {
        label: 'RSI',
        data: rsi,
        borderColor: '#9C27B0',
        backgroundColor: 'rgba(156, 39, 176, 0.1)',
        borderWidth: 2,
        pointRadius: 0,
        tension: 0.1,
        fill: false,
      },
    ],
  };

  const priceChartOptions: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          color: '#ffffff',
        },
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#ffffff',
        bodyColor: '#ffffff',
        borderColor: '#333',
        borderWidth: 1,
      },
    },
    scales: {
      x: {
        ticks: {
          color: '#ffffff',
          maxTicksLimit: 10,
        },
        grid: {
          color: 'rgba(255, 255, 255, 0.1)',
        },
      },
      y: {
        ticks: {
          color: '#ffffff',
        },
        grid: {
          color: 'rgba(255, 255, 255, 0.1)',
        },
      },
    },
    interaction: {
      mode: 'index' as const,
      intersect: false,
    },
  };

  const rsiChartOptions: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          color: '#ffffff',
        },
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#ffffff',
        bodyColor: '#ffffff',
        borderColor: '#333',
        borderWidth: 1,
      },
    },
    scales: {
      x: {
        ticks: {
          color: '#ffffff',
          maxTicksLimit: 10,
        },
        grid: {
          color: 'rgba(255, 255, 255, 0.1)',
        },
      },
      y: {
        min: 0,
        max: 100,
        ticks: {
          color: '#ffffff',
        },
        grid: {
          color: 'rgba(255, 255, 255, 0.1)',
        },
      },
    },
  };

  const currentRSI = rsi[rsi.length - 1];
  const currentMA20 = ma20[ma20.length - 1];
  const currentMA50 = ma50[ma50.length - 1];
  const currentPrice = prices[prices.length - 1];

  return (
    <Box sx={{ p: 3 }}>
      {/* Technical Indicators Summary */}
      <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
        <Card sx={{ bgcolor: 'background.paper', flex: '1 1 200px' }}>
          <CardContent>
            <Typography variant="h6" color="primary" gutterBottom>
              RSI (14)
            </Typography>
            <Typography variant="h4" sx={{ mb: 1 }}>
              {currentRSI ? currentRSI.toFixed(1) : 'N/A'}
            </Typography>
            <Typography 
              variant="body2" 
              color={
                currentRSI && currentRSI > 70 ? 'error.main' :
                currentRSI && currentRSI < 30 ? 'success.main' : 'text.secondary'
              }
            >
              {currentRSI && currentRSI > 70 ? 'Overbought' :
               currentRSI && currentRSI < 30 ? 'Oversold' : 'Neutral'}
            </Typography>
          </CardContent>
        </Card>

        <Card sx={{ bgcolor: 'background.paper', flex: '1 1 200px' }}>
          <CardContent>
            <Typography variant="h6" color="primary" gutterBottom>
              MA20
            </Typography>
            <Typography variant="h4" sx={{ mb: 1 }}>
              ${currentMA20 ? currentMA20.toFixed(2) : 'N/A'}
            </Typography>
            <Typography 
              variant="body2" 
              color={currentPrice > (currentMA20 || 0) ? 'success.main' : 'error.main'}
            >
              {currentPrice > (currentMA20 || 0) ? 'Above MA20' : 'Below MA20'}
            </Typography>
          </CardContent>
        </Card>

        <Card sx={{ bgcolor: 'background.paper', flex: '1 1 200px' }}>
          <CardContent>
            <Typography variant="h6" color="primary" gutterBottom>
              MA50
            </Typography>
            <Typography variant="h4" sx={{ mb: 1 }}>
              ${currentMA50 ? currentMA50.toFixed(2) : 'N/A'}
            </Typography>
            <Typography 
              variant="body2" 
              color={currentPrice > (currentMA50 || 0) ? 'success.main' : 'error.main'}
            >
              {currentPrice > (currentMA50 || 0) ? 'Above MA50' : 'Below MA50'}
            </Typography>
          </CardContent>
        </Card>

        <Card sx={{ bgcolor: 'background.paper', flex: '1 1 200px' }}>
          <CardContent>
            <Typography variant="h6" color="primary" gutterBottom>
              Signal
            </Typography>
            <Typography variant="h4" sx={{ mb: 1 }}>
              {technicalAnalysis?.signal || 'HOLD'}
            </Typography>
            <Typography 
              variant="body2" 
              color={
                (technicalAnalysis?.signal || 'HOLD') === 'BUY' ? 'success.main' :
                (technicalAnalysis?.signal || 'HOLD') === 'SELL' ? 'error.main' : 'warning.main'
              }
            >
              Based on indicators
            </Typography>
          </CardContent>
        </Card>
      </Box>

      {/* Price Chart with Moving Averages */}
      <Card sx={{ bgcolor: 'background.paper', mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Price Chart with Moving Averages
          </Typography>
          <Box sx={{ height: 400 }}>
            <Line data={priceChartData} options={priceChartOptions} />
          </Box>
        </CardContent>
      </Card>

      {/* RSI Chart */}
      <Card sx={{ bgcolor: 'background.paper' }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Relative Strength Index (RSI)
          </Typography>
          <Box sx={{ height: 300 }}>
            <Line data={rsiChartData} options={rsiChartOptions} />
          </Box>
          <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center', gap: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Box sx={{ width: 12, height: 2, bgcolor: 'error.main' }} />
              <Typography variant="body2">Overbought (70+)</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Box sx={{ width: 12, height: 2, bgcolor: 'success.main' }} />
              <Typography variant="body2">Oversold (30-)</Typography>
            </Box>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};