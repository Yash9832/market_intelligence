import React, { useState } from 'react';
import {
  ThemeProvider,
  createTheme,
  CssBaseline,
  Box,
  AppBar,
  Toolbar,
  Typography,
  Tabs,
  Tab,
  IconButton,
  Tooltip,
  Container,
  Drawer,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
  ListSubheader,
  Avatar,
} from '@mui/material';
import {
  Search,
  TrendingUp,
  Analytics,
  SmartToy,
  Menu as MenuIcon,
  ChevronLeft,
  ChevronRight,
} from '@mui/icons-material';

import SearchComponent from './components/SearchComponent';
import MarketOverview from './components/MarketOverview';
import StockAnalyzer from './components/StockAnalyzer';
import ChatbotPage from './components/ChatbotPage';
import { AppStateProvider } from './contexts/AppStateContext';

// Clean, minimal theme
const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#2196f3',
    },
    background: {
      default: '#0a0a0a',
      paper: '#1a1a1a',
    },
    text: {
      primary: '#ffffff',
      secondary: '#b0b0b0',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", sans-serif',
    h4: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 500,
    },
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          border: '1px solid rgba(255, 255, 255, 0.1)',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#1a1a1a',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
          backdropFilter: 'saturate(180%) blur(8px)',
        },
      },
    },
  },
});

function App() {
  const [currentTab, setCurrentTab] = useState(1); // 0: search, 1: market, 2: analysis, 3: chatbot
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleStockSelect = (symbol: string) => {
    setSelectedSymbol(symbol);
    setCurrentTab(2); // Switch to Stock Analyzer
  };

  const renderCurrentView = () => {
    switch (currentTab) {
      case 0:
        return <SearchComponent onStockSelect={handleStockSelect} />;
      case 1:
        return <MarketOverview onStockSelect={handleStockSelect} />;
      case 2:
        return <StockAnalyzer selectedSymbol={selectedSymbol} onSymbolChange={setSelectedSymbol} />;
      case 3:
        return <ChatbotPage />;
      default:
        return <MarketOverview onStockSelect={handleStockSelect} />;
    }
  };

  const navItems = [
    { id: 0, label: 'Search', icon: <Search /> },
    { id: 1, label: 'Market', icon: <TrendingUp /> },
    { id: 2, label: 'Analysis', icon: <Analytics /> },
    { id: 3, label: 'Chatbot', icon: <SmartToy /> },
  ];

  const drawerWidth = sidebarOpen ? 220 : 72;

  return (
    <AppStateProvider>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Box sx={{ width:'100vw', height: '100vh', display: 'flex', flexDirection: 'column' }}>
          <AppBar 
            position="sticky" 
            elevation={0}
            sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}
          >
            <Toolbar>
              {/* Mobile hamburger */}
              <Box sx={{ display: { xs: 'inline-flex', md: 'none' }, mr: 1 }}>
                <IconButton color="inherit" edge="start" onClick={() => setSidebarOpen((v) => !v)} aria-label="Toggle navigation">
                  <MenuIcon />
                </IconButton>
              </Box>
              {/* Desktop chevrons */}
              <Box sx={{ display: { xs: 'none', md: 'inline-flex' }, mr: 1 }}>
                <Tooltip title={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}>
                  <IconButton color="inherit" edge="start" onClick={() => setSidebarOpen((v) => !v)} aria-label="Toggle sidebar">
                    {sidebarOpen ? <ChevronLeft /> : <ChevronRight />}
                  </IconButton>
                </Tooltip>
              </Box>
              <TrendingUp sx={{ mr: 2 }} />
              <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                Financial Dashboard
              </Typography>
              {selectedSymbol && (
                <Tooltip title="Currently selected">
                  <Box sx={{ 
                    bgcolor: 'primary.main', 
                    color: 'white',
                    px: 2, 
                    py: 0.5, 
                    borderRadius: 1,
                    fontSize: '0.875rem',
                    fontWeight: 500
                  }}>
                    {selectedSymbol}
                  </Box>
                </Tooltip>
              )}
            </Toolbar>
          </AppBar>

          <Box sx={{ display: 'flex', flex: 1, minHeight: 0 }}>
            {/* Sidebar */}
            <Drawer
              variant="permanent"
              open={sidebarOpen}
              sx={{
                width: { md: drawerWidth },
                flexShrink: 0,
                '& .MuiDrawer-paper': {
                  width: { md: drawerWidth },
                  boxSizing: 'border-box',
                  bgcolor: 'background.paper',
                  borderRight: '1px solid rgba(255, 255, 255, 0.1)',
                  transition: (theme) => theme.transitions.create('width', {
                    easing: theme.transitions.easing.sharp,
                    duration: theme.transitions.duration.shorter,
                  }),
                },
                display: { xs: 'none', md: 'block' }
              }}
            >
              <Toolbar sx={{ justifyContent: sidebarOpen ? 'flex-end' : 'center' }}>
                <IconButton onClick={() => setSidebarOpen((v) => !v)} aria-label={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}>
                  {sidebarOpen ? <ChevronLeft /> : <ChevronRight />}
                </IconButton>
              </Toolbar>
              <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                <List
                  subheader={
                    sidebarOpen ? (
                      <ListSubheader component="div" sx={{ bgcolor: 'transparent', color: 'text.secondary' }}>
                        Navigation
                      </ListSubheader>
                    ) : null
                  }
                  sx={{ px: sidebarOpen ? 1 : 0.5, py: 1 }}
                >
                  {navItems.map((item) => (
                    <ListItemButton
                      key={item.id}
                      selected={currentTab === item.id}
                      onClick={() => setCurrentTab(item.id)}
                      sx={{
                        px: sidebarOpen ? 2 : 1,
                        py: sidebarOpen ? 1.25 : 1,
                        mb: 0.5,
                        justifyContent: sidebarOpen ? 'flex-start' : 'center',
                        '& .MuiListItemIcon-root': { minWidth: sidebarOpen ? 36 : 'auto' },
                        '&.Mui-selected': { bgcolor: 'rgba(33,150,243,0.15)' },
                        '&:hover': { bgcolor: 'rgba(255,255,255,0.05)' }
                      }}
                      aria-label={`Go to ${item.label}`}
                    >
                      <ListItemIcon sx={{ color: 'text.secondary' }}>
                        {item.icon}
                      </ListItemIcon>
                      {sidebarOpen && <ListItemText primary={item.label} />}
                    </ListItemButton>
                  ))}
                </List>
                <Divider sx={{ mt: 'auto' }} />
                <Box sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 1.5 }}>
                  <Avatar sx={{ width: 32, height: 32 }}>U</Avatar>
                  {sidebarOpen && (
                    <Box>
                      <Typography variant="body2" sx={{ lineHeight: 1.1 }}>User</Typography>
                      <Typography variant="caption" color="text.secondary">Pro Member</Typography>
                    </Box>
                  )}
                </Box>
              </Box>
            </Drawer>

            {/* Content */}
            <Box sx={{ flex: 1, overflow: 'auto', bgcolor: 'background.default' }}>
              <Container maxWidth="lg" sx={{ py: 3 }}>
                {renderCurrentView()}
              </Container>
            </Box>
          </Box>
        </Box>
      </ThemeProvider>
    </AppStateProvider>
  );
}

export default App;
