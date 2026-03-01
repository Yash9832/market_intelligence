import React from 'react';
import { Box, Typography, Button } from '@mui/material';

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  actionText?: string;
  onAction?: () => void;
}

const EmptyState: React.FC<EmptyStateProps> = ({ icon, title, description, actionText, onAction }) => {
  return (
    <Box sx={{ textAlign: 'center', py: 8, px: 2 }}>
      {icon && (
        <Box sx={{ mb: 3, '& svg': { fontSize: 64, color: 'text.secondary' } }}>
          {icon}
        </Box>
      )}
      <Typography variant="h5" sx={{ color: 'text.primary', fontWeight: 600, mb: 1 }}>
        {title}
      </Typography>
      {description && (
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          {description}
        </Typography>
      )}
      {actionText && onAction && (
        <Button variant="contained" onClick={onAction}>
          {actionText}
        </Button>
      )}
    </Box>
  );
};

export default EmptyState;


