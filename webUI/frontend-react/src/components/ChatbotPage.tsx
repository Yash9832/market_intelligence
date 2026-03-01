import React, { useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import {
  Box,
  Paper,
  Typography,
  TextField,
  IconButton,
  Avatar,
  Chip,
  CircularProgress,
  Card,
  CardContent,
  InputAdornment,
} from '@mui/material';
import {
  Send,
  SmartToy,
  Person,
  TrendingUp,
  Analytics,
  AttachMoney,
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import ApiService from '../services/api';
import { useMessages } from '../contexts/AppStateContext';
import type { Message } from '../contexts/AppStateContext';

const ChatbotPage: React.FC = () => {
  const {
    messages,
    addMessage,
    clearMessages,
    isLoading,
    setLoading
  } = useMessages();
  
  const [inputValue, setInputValue] = React.useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue,
      timestamp: new Date(),
    };

    addMessage(userMessage);
    setInputValue('');
    setLoading(true);

    try {
      const response = await ApiService.sendChatMessage(
        inputValue,
        messages.slice(-4).map(msg => ({
          role: msg.type === 'user' ? 'user' : 'assistant',
          content: msg.content
        }))
      );

      if (response.success) {
        const { response: aiResponse, chart_data, tool_calls, entities } = response.data;
        
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          type: 'assistant',
          content: aiResponse,
          timestamp: new Date(),
          data: {
            tool_calls,
            entities,
            chart_data
          }
        };

        addMessage(assistantMessage);
        
        // Chart data is now included in the message data
      } else {
        throw new Error(response.message || 'Failed to get response');
      }
    } catch (error: any) {
      let errorContent = 'I\'m sorry, I encountered an error. Please try again.';
      
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        errorContent = 'I\'m sorry, I encountered a timeout of 30000ms exceeded. The AI analysis is taking longer than expected. Please try again, and I\'ll work faster this time.';
      } else if (error.response?.status >= 500) {
        errorContent = 'I\'m experiencing server issues. Please try again in a moment.';
      } else if (error.message) {
        errorContent = `I encountered an error: ${error.message}. Please try again.`;
      }
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: errorContent,
        timestamp: new Date(),
      };
      addMessage(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const formatTimestamp = (timestamp: Date) => {
    return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const renderChart = (symbol: string, data: any) => {
    if (!data.chart_data || data.chart_data.length === 0) return null;

    const chartPoints = data.chart_data.map((point: any) => ({
      date: new Date(point.date).toLocaleDateString(),
      price: point.close,
      volume: point.volume
    }));

    return (
      <Card key={symbol} sx={{ mt: 2, mb: 2 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            {symbol} - Price Chart
          </Typography>
          
          {/* Stock info summary */}
          <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
            <Chip 
              icon={<AttachMoney />} 
              label={`$${data.current_price.toFixed(2)}`} 
              color="primary" 
              variant="outlined" 
            />
            <Chip 
              label={`${data.total_return >= 0 ? '+' : ''}${data.total_return}%`} 
              color={data.total_return >= 0 ? 'success' : 'error'}
              variant="outlined"
            />
            <Chip 
              label={`High: $${data.period_high.toFixed(2)}`} 
              color="info"
              variant="outlined" 
            />
            <Chip 
              label={`Low: $${data.period_low.toFixed(2)}`} 
              color="warning"
              variant="outlined" 
            />
          </Box>

          {/* Price chart */}
          <Box sx={{ height: 300, width: '100%' }}>
            <ResponsiveContainer>
              <LineChart data={chartPoints}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip 
                  labelFormatter={(label: any) => `Date: ${label}`}
                  formatter={(value: any) => [`$${value.toFixed(2)}`, 'Price']}
                />
                <Line 
                  type="monotone" 
                  dataKey="price" 
                  stroke="#2196f3" 
                  strokeWidth={2}
                  dot={{ fill: '#2196f3', strokeWidth: 2, r: 4 }}
                  activeDot={{ r: 6, stroke: '#2196f3', strokeWidth: 2 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </Box>
        </CardContent>
      </Card>
    );
  };

  const renderMessageContent = (message: Message) => {
    const isUser = message.type === 'user';
    return (
      <>
        {isUser ? (
          <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
            {message.content}
          </Typography>
        ) : (
          <Box sx={{
            '& h1, & h2, & h3': { color: '#ffffff', mt: 1, mb: 1 },
            '& p': { color: '#e0e0e0', mb: 1 },
            '& ul': { pl: 3, mb: 1 },
            '& li': { color: '#e0e0e0' },
            '& strong': { color: '#ffffff' },
            '& a': { color: '#64b5f6' },
            '& code': {
              background: '#111',
              padding: '2px 6px',
              borderRadius: '4px',
              fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace'
            },
            '& pre > code': {
              display: 'block',
              padding: '12px',
              overflowX: 'auto'
            }
          }}>
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </Box>
        )}

        {/* Show entities if available */}
        {message.data?.entities && (
          <Box sx={{ mt: 1 }}>
            <Typography variant="caption" color="text.secondary">
              Identified: {message.data.entities.summary}
            </Typography>
          </Box>
        )}

        {/* Show charts if available */}
        {message.data?.chart_data && Object.keys(message.data.chart_data).map(symbol => 
          renderChart(symbol, message.data.chart_data[symbol])
        )}
      </>
    );
  };

  const suggestionPrompts = [
    "Tell me about NVIDIA's recent performance",
    "What's Apple's current stock price?",
    "Analyze Tesla's stock trends",
    "Compare Microsoft and Google stocks",
  ];

  const handleSuggestionClick = (prompt: string) => {
    setInputValue(prompt);
  };

  return (
    <Box sx={{ height: '100%', minHeight: 'calc(100vh - 64px)', display: 'flex', flexDirection: 'column', bgcolor: 'background.default' }}>
      {/* Chat header (subtle) */}
      <Paper elevation={0} sx={{ p: 2, borderBottom: '1px solid', borderColor: 'rgba(255,255,255,0.08)', bgcolor: 'background.paper' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <SmartToy sx={{ color: 'primary.main' }} />
          <Typography variant="h6" component="h1" sx={{ fontWeight: 600 }}>Financial Assistant</Typography>
          <Box sx={{ ml: 'auto', display: 'flex', gap: 1 }}>
            <Chip icon={<Analytics />} label="AI Powered" size="small" />
            <Chip icon={<TrendingUp />} label="Real-time Data" size="small" color="primary" />
          </Box>
        </Box>
      </Paper>

      {/* Messages Area */}
      <Box sx={{ flex: 1, overflow: 'auto', bgcolor: 'background.default' }}>
        <Box sx={{ maxWidth: 860, mx: 'auto', px: 2, py: 2 }}>
          {messages.map((m) => {
            const isUser = m.type === 'user';
            return (
              <Box key={m.id} sx={{ display: 'flex', mb: 2, justifyContent: isUser ? 'flex-end' : 'flex-start' }}>
                {!isUser && (
                  <Avatar sx={{ bgcolor: 'secondary.main', mr: 1, width: 32, height: 32 }}>
                    <SmartToy />
                  </Avatar>
                )}
                <Box sx={{ maxWidth: '85%', display: 'flex', flexDirection: 'column', alignItems: isUser ? 'flex-end' : 'flex-start' }}>
                  <Paper
                    sx={{
                      px: 2,
                      py: 1.25,
                      bgcolor: isUser ? 'primary.main' : 'background.paper',
                      color: isUser ? 'white' : 'text.primary',
                      borderRadius: 2,
                    }}
                  >
                    {renderMessageContent(m)}
                  </Paper>
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
                    {formatTimestamp(m.timestamp)}
                  </Typography>
                </Box>
                {isUser && (
                  <Avatar sx={{ bgcolor: 'primary.main', ml: 1, width: 32, height: 32 }}>
                    <Person />
                  </Avatar>
                )}
              </Box>
            );
          })}

          {isLoading && (
            <Box sx={{ display: 'flex', justifyContent: 'flex-start', mb: 2 }}>
              <Avatar sx={{ bgcolor: 'secondary.main', mr: 1, width: 32, height: 32 }}>
                <SmartToy />
              </Avatar>
              <Paper sx={{ px: 2, py: 1, bgcolor: 'background.paper', borderRadius: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <CircularProgress size={16} sx={{ mr: 1 }} />
                  <Typography variant="body2">Analyzing and fetching data...</Typography>
                </Box>
              </Paper>
            </Box>
          )}

          <div ref={messagesEndRef} />
        </Box>
      </Box>

      {/* Suggestions */}
      {messages.length <= 1 && (
        <Box sx={{ px: 2, py: 1.5, bgcolor: 'background.paper', borderTop: '1px solid', borderColor: 'rgba(255,255,255,0.08)' }}>
          <Box sx={{ maxWidth: 860, mx: 'auto' }}>
            <Typography variant="subtitle2" gutterBottom color="text.secondary">
              Try these prompts:
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {suggestionPrompts.map((prompt, index) => (
                <Chip
                  key={index}
                  label={prompt}
                  onClick={() => handleSuggestionClick(prompt)}
                  variant="outlined"
                  sx={{ cursor: 'pointer' }}
                />
              ))}
            </Box>
          </Box>
        </Box>
      )}

      {/* Input Area */}
      <Paper 
        elevation={3} 
        sx={{ 
          p: 2, 
          borderRadius: 0,
          borderTop: '1px solid',
          borderColor: '#333333',
          bgcolor: '#1a1a1a',
          position: 'sticky',
          bottom: 0,
        }}
      >
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
          <TextField
            fullWidth
            multiline
            maxRows={4}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me about stocks, companies, or market analysis..."
            variant="outlined"
            disabled={isLoading}
            size="small"
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    color="primary"
                    onClick={handleSendMessage}
                    disabled={!inputValue.trim() || isLoading}
                    sx={{ 
                      bgcolor: 'primary.main',
                      color: 'white',
                      '&:hover': { bgcolor: 'primary.dark' },
                      '&:disabled': { bgcolor: 'grey.800', color: 'grey.500' },
                      ml: 1
                    }}
                  >
                    <Send />
                  </IconButton>
                </InputAdornment>
              )
            }}
          />
        </Box>
      </Paper>
    </Box>
  );
};

export default ChatbotPage;