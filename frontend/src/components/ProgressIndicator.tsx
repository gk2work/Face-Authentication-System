import { Box, LinearProgress, Typography } from '@mui/material';

interface ProgressIndicatorProps {
  progress: number;
  message?: string;
  showPercentage?: boolean;
}

export const ProgressIndicator = ({ 
  progress, 
  message,
  showPercentage = true 
}: ProgressIndicatorProps) => {
  return (
    <Box sx={{ width: '100%' }}>
      {message && (
        <Typography variant="body2" color="text.secondary" gutterBottom>
          {message}
        </Typography>
      )}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Box sx={{ width: '100%' }}>
          <LinearProgress 
            variant="determinate" 
            value={progress} 
            sx={{ height: 8, borderRadius: 4 }}
          />
        </Box>
        {showPercentage && (
          <Box sx={{ minWidth: 45 }}>
            <Typography variant="body2" color="text.secondary">
              {`${Math.round(progress)}%`}
            </Typography>
          </Box>
        )}
      </Box>
    </Box>
  );
};
