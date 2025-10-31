import { Card, CardContent, Box, Typography, CircularProgress } from '@mui/material';
import { TrendingUp, TrendingDown } from '@mui/icons-material';

interface StatCardProps {
  title: string;
  value: number | string;
  icon: React.ReactElement;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  loading?: boolean;
  onClick?: () => void;
}

export const StatCard = ({ title, value, icon, trend, loading, onClick }: StatCardProps) => {
  return (
    <Card
      sx={{
        height: '100%',
        cursor: onClick ? 'pointer' : 'default',
        transition: 'transform 0.2s, box-shadow 0.2s',
        '&:hover': onClick
          ? {
              transform: 'translateY(-4px)',
              boxShadow: 4,
            }
          : {},
      }}
      onClick={onClick}
    >
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
          <Box sx={{ flex: 1 }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {title}
            </Typography>
            {loading ? (
              <CircularProgress size={24} sx={{ my: 1 }} />
            ) : (
              <Typography variant="h4" component="div" fontWeight={600} sx={{ mb: 1 }}>
                {value}
              </Typography>
            )}
            {trend && !loading && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                {trend.isPositive ? (
                  <TrendingUp fontSize="small" color="success" />
                ) : (
                  <TrendingDown fontSize="small" color="error" />
                )}
                <Typography
                  variant="body2"
                  color={trend.isPositive ? 'success.main' : 'error.main'}
                  fontWeight={500}
                >
                  {trend.value > 0 ? '+' : ''}
                  {trend.value}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  vs last period
                </Typography>
              </Box>
            )}
          </Box>
          <Box
            sx={{
              width: 56,
              height: 56,
              borderRadius: 2,
              bgcolor: 'primary.main',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white',
            }}
          >
            {icon}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};
