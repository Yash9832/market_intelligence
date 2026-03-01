import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Box, Paper, Typography, Chip, Divider, IconButton, TextField, Button, Tooltip } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';

type NewsArticle = {
  id: string;
  title: string;
  description: string;
  link: string;
  source: string;
  published?: string;
  matched_keywords: string[];
  timestamp: string;
};

interface LiveNewsFeedProps {
  symbol: string | null;
  companyName?: string | null;
  height?: number | string; // allow parent-controlled height
  maxItems?: number;
}

const LiveNewsFeed: React.FC<LiveNewsFeedProps> = ({ symbol, companyName, height = 520, maxItems = 100 }) => {
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [connected, setConnected] = useState(false);
  const [keywords, setKeywords] = useState<string[]>([]);
  const [input, setInput] = useState<string>('');
  const wsRef = useRef<WebSocket | null>(null);

  const sessionId = useMemo(() => {
    return 'user_' + Math.random().toString(36).slice(2, 11);
  }, []);

  const wsUrl = useMemo(() => {
    const base = 'localhost:8000';
    return `ws://${base}/stocks/news/ws/${sessionId}`;
  }, [sessionId]);

  useEffect(() => {
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      // If we already have keywords, re-send them
      if (keywords.length > 0) {
        ws.send(JSON.stringify({ type: 'set_keywords', keywords }));
        setTimeout(() => ws.send(JSON.stringify({ type: 'get_recent' })), 300);
      }
    };
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'new_article' || data.type === 'recent_article') {
        const article: NewsArticle = data.article;
        setArticles((prev) => {
          const exists = prev.some((a) => a.id === article.id);
          const next = exists ? prev : [article, ...prev].slice(0, maxItems);
          return next;
        });
      } else if (data.type === 'keywords_updated') {
        // no-op
      }
    };

    return () => {
      ws.close();
    };
  }, [wsUrl]);

  // Auto-send keywords whenever they change (no need to click Apply)
  useEffect(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN && keywords.length > 0) {
      wsRef.current.send(JSON.stringify({ type: 'set_keywords', keywords }));
      setTimeout(() => wsRef.current?.send(JSON.stringify({ type: 'get_recent' })), 300);
    }
  }, [keywords]);

  useEffect(() => {
    // Auto-set keywords from symbol and company name (improves matching)
    if (symbol) {
      const symbolUpper = symbol.toUpperCase();
      const map: Record<string, string[]> = {
        AAPL: ['Apple', 'iPhone', 'Mac', 'Tim Cook'],
        MSFT: ['Microsoft', 'Windows', 'Azure', 'Satya Nadella'],
        GOOGL: ['Google', 'Alphabet', 'Android', 'Sundar Pichai'],
        TSLA: ['Tesla', 'Elon Musk', 'EV', 'Gigafactory'],
        AMZN: ['Amazon', 'AWS', 'Prime', 'Jeff Bezos'],
        META: ['Meta', 'Facebook', 'Instagram', 'Mark Zuckerberg'],
        NFLX: ['Netflix', 'streaming', 'Reed Hastings'],
        NVDA: ['NVIDIA', 'Nvidia', 'GPU', 'Jensen Huang'],
      };
      const mapped = map[symbolUpper] || [];
      const defaultKeywords = Array.from(
        new Set([
          ...mapped,
          ...(companyName ? [companyName] : []),
        ])
      );
      setKeywords(defaultKeywords);
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'set_keywords', keywords: defaultKeywords }));
        setTimeout(() => wsRef.current?.send(JSON.stringify({ type: 'get_recent' })), 300);
      }
    }
  }, [symbol, companyName]);

  const applyKeywords = () => {
    const parsed = input
      .split(',')
      .map((k) => k.trim())
      .filter((k) => k.length > 0);
    const keys = parsed.length > 0 ? parsed : keywords;
    setKeywords(keys);
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'set_keywords', keywords: keys }));
      setTimeout(() => wsRef.current?.send(JSON.stringify({ type: 'get_recent' })), 300);
    }
  };

  const clearArticle = (id: string) => {
    setArticles((prev) => prev.filter((a) => a.id !== id));
  };

  return (
    <Paper sx={{ p: 2, height, display: 'flex', flexDirection: 'column', gap: 1, border: '1px solid rgba(255,255,255,0.1)' }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Typography variant="h6">Live News</Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: connected ? 'success.main' : 'error.main' }} />
          <Typography variant="caption" color="text.secondary">{connected ? 'Connected' : 'Disconnected'}</Typography>
        </Box>
      </Box>
      {/* Controls */}
      <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
        <TextField
          size="small"
          placeholder="Add more keywords (comma-separated)"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          fullWidth
        />
        <Button variant="contained" onClick={applyKeywords}>Apply</Button>
      </Box>
      <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', my: 0.5 }}>
        {keywords.map((k) => (
          <Chip key={k} label={k} size="small" />
        ))}
      </Box>
      <Divider />
      {/* List */}
      <Box sx={{ mt: 1, display: 'flex', flexDirection: 'column', gap: 1, overflowY: 'auto' }}>
        {articles.length === 0 && (
          <Typography variant="body2" color="text.secondary">
            No articles yet. Keywords are set to: {keywords.join(', ') || 'none'}
          </Typography>
        )}
        {articles.map((a) => (
          <Paper key={a.id} sx={{ p: 1.25, position: 'relative', display: 'grid', gridTemplateColumns: '1fr auto', gap: 0.5 }}>
            <Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                <Chip label={a.source} size="small" color="primary" variant="outlined" />
                <Typography variant="caption" color="text.secondary">
                  {new Date(a.published || a.timestamp).toLocaleString()}
                </Typography>
              </Box>
              <Typography variant="subtitle2" sx={{ mt: 0 }}>
                <a href={a.link} target="_blank" rel="noreferrer" style={{ textDecoration: 'none' }}>
                  {a.title}
                </a>
              </Typography>
              <Typography
                variant="body2"
                color="text.secondary"
                sx={{ mt: 0.25, display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}
              >
                {a.description}
              </Typography>
              <Box sx={{ mt: 0.5, display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                {a.matched_keywords.map((k) => (
                  <Chip key={k} label={k} size="small" color="warning" />
                ))}
              </Box>
            </Box>
            <Tooltip title="Hide">
              <IconButton size="small" onClick={() => clearArticle(a.id)} sx={{ alignSelf: 'flex-start' }}>
                <CloseIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Paper>
        ))}
      </Box>
    </Paper>
  );
};

export default LiveNewsFeed;


