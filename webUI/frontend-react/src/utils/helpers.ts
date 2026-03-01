/**
 * Format large numbers for display
 */
export const formatNumber = (value: number | null | undefined): string => {
  if (!value || value === 0) {
    return "N/A";
  }
  
  const absValue = Math.abs(value);
  
  if (absValue >= 1e12) {
    return `$${(value / 1e12).toFixed(2)}T`;
  } else if (absValue >= 1e9) {
    return `$${(value / 1e9).toFixed(2)}B`;
  } else if (absValue >= 1e6) {
    return `$${(value / 1e6).toFixed(2)}M`;
  } else if (absValue >= 1e3) {
    return `$${(value / 1e3).toFixed(2)}K`;
  } else {
    return `$${value.toFixed(2)}`;
  }
};

/**
 * Format currency values
 */
export const formatCurrency = (value: number | null | undefined, currency: string = "USD"): string => {
  if (!value) {
    return "N/A";
  }
  
  if (currency === "INR") {
    return `₹${value.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
  } else if (currency === "USD") {
    return `$${value.toLocaleString('en-US', { maximumFractionDigits: 2 })}`;
  } else {
    return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
  }
};

/**
 * Get color for price changes
 */
export const getPriceChangeColor = (changePercent: number): string => {
  if (changePercent > 0) {
    return "#4caf50"; // Green for positive
  } else if (changePercent < 0) {
    return "#f44336"; // Red for negative
  } else {
    return "#9e9e9e"; // Gray for neutral
  }
};

/**
 * Get arrow symbol for price changes
 */
export const getPriceChangeArrow = (changePercent: number): string => {
  if (changePercent > 0) {
    return "↑";
  } else if (changePercent < 0) {
    return "↓";
  } else {
    return "→";
  }
};

/**
 * Format percentage values
 */
export const formatPercentage = (value: number | null | undefined): string => {
  if (value === null || value === undefined) {
    return "N/A";
  }
  return `${value.toFixed(2)}%`;
};

/**
 * Debounce function for search input
 */
export const debounce = <T extends (...args: any[]) => void>(
  func: T,
  delay: number
): ((...args: Parameters<T>) => void) => {
  let timeoutId: ReturnType<typeof setTimeout>;
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), delay);
  };
};

/**
 * Check if API is available (fallback helper)
 */
export const isApiAvailable = async (): Promise<boolean> => {
  try {
    const response = await fetch('http://localhost:8000/health', {
      method: 'GET',
      timeout: 5000,
    } as RequestInit);
    return response.ok;
  } catch {
    return false;
  }
};

/**
 * Safe JSON parse
 */
export const safeJsonParse = <T>(jsonString: string | null, fallback: T): T => {
  if (!jsonString) return fallback;
  
  try {
    return JSON.parse(jsonString);
  } catch {
    return fallback;
  }
};

/**
 * Format date for display
 */
export const formatDate = (dateString: string): string => {
  try {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  } catch {
    return dateString;
  }
};

/**
 * Generate random ID for keys
 */
export const generateId = (): string => {
  return Math.random().toString(36).substring(2, 9);
};

/**
 * Validate stock symbol format
 */
export const isValidStockSymbol = (symbol: string): boolean => {
  // Basic validation for stock symbols (alphanumeric, dots, dashes)
  const symbolPattern = /^[A-Z0-9.-]+$/;
  return symbolPattern.test(symbol.toUpperCase()) && symbol.length >= 1 && symbol.length <= 10;
};