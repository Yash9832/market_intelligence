import React, { useState } from 'react';
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
import { 
  Box, 
  Typography, 
  Card, 
  CardContent, 
  Button, 
  TextField, 
  CircularProgress,
  Alert
} from '@mui/material';
import type { PredictionData, HistoricalData } from '../types';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface PredictionChartProps {
  symbol?: string;
  historicalData: HistoricalData[];
  predictions: PredictionData | null;
  onFetchPredictions: (days: number) => void;
  loading: boolean;
}

export const PredictionChart: React.FC<PredictionChartProps> = ({ 
  symbol,
  historicalData, 
  predictions,
  onFetchPredictions,
  loading
}) => {
  const [predictionDays, setPredictionDays] = useState<number>(30);
  const [error, setError] = useState<string | null>(null);

  const handleFetchPredictions = () => {
    if (symbol && predictionDays > 0 && predictionDays <= 365) {
      try {
        setError(null);
        console.log(`Requesting predictions for ${symbol} with ${predictionDays} days`);
        onFetchPredictions(predictionDays);
      } catch (err) {
        console.error('Error in handleFetchPredictions:', err);
        setError('Failed to generate predictions. Please try again.');
      }
    }
  };

  // Prepare chart data combining historical and prediction data
  const chartData = React.useMemo(() => {
    if (!historicalData || historicalData.length === 0) return null;

    const historicalDates = historicalData.map(d => d.date);
    const historicalPrices = historicalData.map(d => d.close);

    let predictionDates: string[] = [];
    let predictionPrices: (number | null)[] = [];
    let upperBounds: (number | null)[] = [];
    let lowerBounds: (number | null)[] = [];

    if (predictions && predictions.predictions) {
      predictionDates = predictions.predictions.map(p => p.date);
      predictionPrices = predictions.predictions.map(p => p.predicted_price);
      upperBounds = predictions.predictions.map(p => p.upper_bound);
      lowerBounds = predictions.predictions.map(p => p.lower_bound);
    }

    // Combine dates
    const allDates = [...historicalDates, ...predictionDates];
    
    // Prepare price data (historical + predictions)
    const historicalWithNulls = [...historicalPrices, ...Array(predictionDates.length).fill(null)];
    const predictionWithNulls = [...Array(historicalDates.length).fill(null), ...predictionPrices];
    const upperBoundsWithNulls = [...Array(historicalDates.length).fill(null), ...upperBounds];
    const lowerBoundsWithNulls = [...Array(historicalDates.length).fill(null), ...lowerBounds];

    return {
      labels: allDates,
      datasets: [
        {
          label: 'Historical Price',
          data: historicalWithNulls,
          borderColor: '#2196F3',
          backgroundColor: 'rgba(33, 150, 243, 0.1)',
          borderWidth: 2,
          pointRadius: 0,
          tension: 0.1,
        },
        {
          label: 'Predicted Price',
          data: predictionWithNulls,
          borderColor: '#FF5722',
          backgroundColor: 'rgba(255, 87, 34, 0.1)',
          borderWidth: 2,
          pointRadius: 0,
          tension: 0.1,
          borderDash: [5, 5],
        },
        {
          label: 'Upper Confidence',
          data: upperBoundsWithNulls,
          borderColor: 'rgba(76, 175, 80, 0.3)',
          backgroundColor: 'transparent',
          borderWidth: 1,
          pointRadius: 0,
          tension: 0.1,
          fill: false,
        },
        {
          label: 'Lower Confidence',
          data: lowerBoundsWithNulls,
          borderColor: 'rgba(76, 175, 80, 0.3)',
          backgroundColor: 'rgba(76, 175, 80, 0.1)',
          borderWidth: 1,
          pointRadius: 0,
          tension: 0.1,
          fill: '-1', // Fill between this and previous dataset
        },
      ],
    };
  }, [historicalData, predictions]);

  const chartOptions: ChartOptions<'line'> = {
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
          callback: function(value) {
            return '$' + Number(value).toFixed(2);
          },
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

  return (
    <Box sx={{ p: 3 }}>
      {/* Prediction Controls */}
      <Card sx={{ bgcolor: 'background.paper', mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Generate Price Predictions
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Use Prophet ML model to predict future stock prices
          </Typography>
          
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
            <TextField
              label="Prediction Days"
              type="number"
              value={predictionDays}
              onChange={(e) => setPredictionDays(Math.max(1, Math.min(365, parseInt(e.target.value) || 1)))}
              variant="outlined"
              size="small"
              sx={{ minWidth: 150 }}
              inputProps={{
                min: 1,
                max: 365,
              }}
            />
            <Button
              variant="contained"
              onClick={handleFetchPredictions}
              disabled={loading || !symbol}
              startIcon={loading ? <CircularProgress size={20} /> : undefined}
            >
              {loading ? 'Generating...' : 'Generate Predictions'}
            </Button>
          </Box>

          {!symbol && (
            <Alert severity="info" sx={{ mt: 2 }}>
              Please search for a stock symbol first
            </Alert>
          )}

          {error && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {error}
            </Alert>
          )}

          {loading && (
            <Alert severity="info" sx={{ mt: 2 }}>
              Generating predictions... This may take up to 2 minutes.
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Prediction Results */}
      {predictions && (
        <Box sx={{ mb: 3 }}>
          <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
            <Card sx={{ bgcolor: 'background.paper', flex: '1 1 200px' }}>
              <CardContent>
                <Typography variant="h6" color="primary" gutterBottom>
                  Current Price
                </Typography>
                <Typography variant="h4" sx={{ mb: 1 }}>
                  ${predictions.current_price.toFixed(2)}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {symbol?.toUpperCase()}
                </Typography>
              </CardContent>
            </Card>

            <Card sx={{ bgcolor: 'background.paper', flex: '1 1 200px' }}>
              <CardContent>
                <Typography variant="h6" color="primary" gutterBottom>
                  Predicted ({predictions.forecast_days}d)
                </Typography>
                <Typography variant="h4" sx={{ mb: 1 }}>
                  ${predictions.predicted_price.toFixed(2)}
                </Typography>
                <Typography 
                  variant="body2" 
                  color={predictions.price_change >= 0 ? 'success.main' : 'error.main'}
                >
                  {predictions.price_change >= 0 ? '+' : ''}${predictions.price_change.toFixed(2)} 
                  ({predictions.price_change_percent.toFixed(2)}%)
                </Typography>
              </CardContent>
            </Card>

            <Card sx={{ bgcolor: 'background.paper', flex: '1 1 200px' }}>
              <CardContent>
                <Typography variant="h6" color="primary" gutterBottom>
                  Confidence Range
                </Typography>
                <Typography variant="h6" sx={{ mb: 1 }}>
                  ${predictions.confidence_lower.toFixed(2)} - ${predictions.confidence_upper.toFixed(2)}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  95% confidence interval
                </Typography>
              </CardContent>
            </Card>

            <Card sx={{ bgcolor: 'background.paper', flex: '1 1 200px' }}>
              <CardContent>
                <Typography variant="h6" color="primary" gutterBottom>
                  Short-term Outlook
                </Typography>
                <Typography variant="body1" sx={{ mb: 1 }}>
                  1D: ${predictions.day_1.toFixed(2)}
                </Typography>
                <Typography variant="body1" sx={{ mb: 1 }}>
                  7D: ${predictions.week_1.toFixed(2)}
                </Typography>
                <Typography variant="body1">
                  30D: ${predictions.month_1.toFixed(2)}
                </Typography>
              </CardContent>
            </Card>
          </Box>
        </Box>
      )}

      {/* Prediction Chart */}
      {chartData && (
        <Card sx={{ bgcolor: 'background.paper' }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Price Prediction Chart
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Historical prices (solid line) and predicted prices (dashed line) with confidence intervals
            </Typography>
            <Box sx={{ height: 500 }}>
              <Line data={chartData} options={chartOptions} />
            </Box>
          </CardContent>
        </Card>
      )}

      {!predictions && !loading && (
        <Card sx={{ bgcolor: 'background.paper' }}>
          <CardContent sx={{ textAlign: 'center', py: 6 }}>
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No predictions available
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Click "Generate Predictions" to create AI-powered price forecasts
            </Typography>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};