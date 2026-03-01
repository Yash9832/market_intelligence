import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';
import type { HistoricalData } from '../types';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

interface VolumeChartProps {
  data: HistoricalData[];
  title?: string;
}

const VolumeChart: React.FC<VolumeChartProps> = ({ data, title = 'Volume' }) => {
  // Take last 30 days of data to avoid overcrowding
  const recentData = data.slice(-30);
  
  const chartData = {
    labels: recentData.map(item => new Date(item.date).toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric' 
    })),
    datasets: [
      {
        label: 'Volume',
        data: recentData.map(item => item.volume),
        backgroundColor: 'rgba(33, 150, 243, 0.6)',
        borderColor: 'rgba(33, 150, 243, 1)',
        borderWidth: 1,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      title: {
        display: true,
        text: title,
        color: '#b0b0b0',
        font: {
          size: 16,
          weight: 'bold' as const,
        },
      },
      tooltip: {
        backgroundColor: 'rgba(26, 26, 26, 0.95)',
        titleColor: '#ffffff',
        bodyColor: '#ffffff',
        borderColor: 'rgba(255, 255, 255, 0.1)',
        borderWidth: 1,
        callbacks: {
          label: function(context: any) {
            return `Volume: ${(context.parsed.y / 1000000).toFixed(1)}M`;
          }
        }
      },
    },
    scales: {
      x: {
        grid: {
          color: 'rgba(255, 255, 255, 0.1)',
        },
        ticks: {
          color: '#b0b0b0',
          maxTicksLimit: 8,
        },
      },
      y: {
        grid: {
          color: 'rgba(255, 255, 255, 0.1)',
        },
        ticks: {
          color: '#b0b0b0',
          callback: function(value: any) {
            return (value / 1000000).toFixed(0) + 'M';
          },
        },
      },
    },
  };

  return (
    <div style={{ height: '200px', width: '100%' }}>
      <Bar data={chartData} options={options} />
    </div>
  );
};

export default VolumeChart;