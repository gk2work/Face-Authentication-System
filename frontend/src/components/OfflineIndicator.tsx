import { Alert, Snackbar, Slide } from '@mui/material';
import { WifiOff as WifiOffIcon } from '@mui/icons-material';
import { useOnlineStatus } from '@/hooks/useOnlineStatus';

export const OfflineIndicator = () => {
  const isOnline = useOnlineStatus();

  return (
    <Snackbar
      open={!isOnline}
      anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      TransitionComponent={Slide}
    >
      <Alert 
        severity="warning" 
        icon={<WifiOffIcon />}
        sx={{ width: '100%' }}
      >
        You are currently offline. Some features may not be available.
      </Alert>
    </Snackbar>
  );
};
