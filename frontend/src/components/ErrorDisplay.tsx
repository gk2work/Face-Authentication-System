import { Alert, AlertTitle, Button } from '@mui/material';
import { Refresh as RefreshIcon } from '@mui/icons-material';

interface ErrorDisplayProps {
  error: Error | string;
  onRetry?: () => void;
  title?: string;
  severity?: 'error' | 'warning' | 'info';
}

export const ErrorDisplay = ({ 
  error, 
  onRetry, 
  title = 'Error',
  severity = 'error'
}: ErrorDisplayProps) => {
  const errorMessage = typeof error === 'string' ? error : error.message;

  return (
    <Alert 
      severity={severity}
      action={
        onRetry && (
          <Button
            color="inherit"
            size="small"
            startIcon={<RefreshIcon />}
            onClick={onRetry}
          >
            Retry
          </Button>
        )
      }
    >
      <AlertTitle>{title}</AlertTitle>
      {errorMessage}
    </Alert>
  );
};
