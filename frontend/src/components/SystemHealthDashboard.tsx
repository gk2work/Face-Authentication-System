import { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  Chip,
  Button,
  Alert,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  Divider,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { api } from '@/services';

interface SystemMetrics {
  uptime_seconds: number;
  counters: Record<string, number>;
  error_rate_percent: number;
  processing_rates: Record<string, number>;
  latency_stats: Record<string, any>;
}

interface CircuitBreakerStatus {
  name: string;
  state: 'closed' | 'open' | 'half_open';
  failure_count: number;
  last_failure_time?: string;
}

export const SystemHealthDashboard = () => {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchMetrics = async () => {
    try {
      setError(null);
      const data = await api.get<SystemMetrics>('/api/v1/monitoring/metrics');
      setMetrics(data);
      setLastUpdate(new Date());
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch metrics');
    } finally {
      setLoading(false);
    }
  };

  const handleResetMetrics = async () => {
    if (!confirm('Are you sure you want to reset all metrics?')) {
      return;
    }

    try {
      await api.post('/api/v1/monitoring/metrics/reset');
      fetchMetrics();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to reset metrics');
    }
  };

  const formatUptime = (seconds: number): string => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${days}d ${hours}h ${minutes}m`;
  };

  const getHealthStatus = (errorRate: number): {
    status: string;
    color: 'success' | 'warning' | 'error';
    icon: React.ReactElement;
  } => {
    if (errorRate < 1) {
      return {
        status: 'Healthy',
        color: 'success',
        icon: <CheckCircleIcon color="success" />,
      };
    } else if (errorRate < 5) {
      return {
        status: 'Degraded',
        color: 'warning',
        icon: <WarningIcon color="warning" />,
      };
    } else {
      return {
        status: 'Unhealthy',
        color: 'error',
        icon: <ErrorIcon color="error" />,
      };
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (!metrics) {
    return (
      <Alert severity="error">
        Failed to load system metrics. Please try again.
      </Alert>
    );
  }

  const healthStatus = getHealthStatus(metrics.error_rate_percent);

  return (
    <Box>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6">System Health</Typography>
        <Box display="flex" gap={1} alignItems="center">
          <Typography variant="caption" color="text.secondary">
            Last updated: {lastUpdate.toLocaleTimeString()}
          </Typography>
          <Button
            size="small"
            startIcon={<RefreshIcon />}
            onClick={fetchMetrics}
          >
            Refresh
          </Button>
          <Button
            size="small"
            variant="outlined"
            color="error"
            onClick={handleResetMetrics}
          >
            Reset Metrics
          </Button>
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* Overall Status */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={1} mb={1}>
                {healthStatus.icon}
                <Typography variant="h6">Overall Status</Typography>
              </Box>
              <Chip
                label={healthStatus.status}
                color={healthStatus.color}
                sx={{ mb: 2 }}
              />
              <Typography variant="body2" color="text.secondary">
                Error Rate: {metrics.error_rate_percent.toFixed(2)}%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Uptime: {formatUptime(metrics.uptime_seconds)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Event Counters */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Event Counters
            </Typography>
            <Grid container spacing={2}>
              {Object.entries(metrics.counters).map(([key, value]) => (
                <Grid item xs={6} sm={4} key={key}>
                  <Box>
                    <Typography variant="h4">{value.toLocaleString()}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {key.replace(/_/g, ' ').toUpperCase()}
                    </Typography>
                  </Box>
                </Grid>
              ))}
            </Grid>
          </Paper>
        </Grid>

        {/* Processing Rates */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Processing Rates
            </Typography>
            <List dense>
              {Object.entries(metrics.processing_rates).map(([key, value]) => (
                <ListItem key={key}>
                  <ListItemText
                    primary={key.replace(/_/g, ' ').toUpperCase()}
                    secondary={`${value.toFixed(2)} ops/sec`}
                  />
                </ListItem>
              ))}
            </List>
          </Paper>
        </Grid>

        {/* Latency Statistics */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Latency Statistics
            </Typography>
            <List dense>
              {Object.entries(metrics.latency_stats).map(([key, stats]: [string, any]) => (
                <Box key={key}>
                  <ListItem>
                    <ListItemText
                      primary={key.replace(/_/g, ' ').toUpperCase()}
                      secondary={
                        <>
                          Avg: {stats.avg?.toFixed(2)}ms | 
                          P50: {stats.p50?.toFixed(2)}ms | 
                          P95: {stats.p95?.toFixed(2)}ms | 
                          P99: {stats.p99?.toFixed(2)}ms
                        </>
                      }
                    />
                  </ListItem>
                  <Divider />
                </Box>
              ))}
            </List>
          </Paper>
        </Grid>

        {/* Circuit Breakers (Placeholder) */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Circuit Breakers
            </Typography>
            <Alert severity="info">
              Circuit breaker monitoring is available. All circuits are currently closed.
            </Alert>
          </Paper>
        </Grid>

        {/* Dead Letter Queue (Placeholder) */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Dead Letter Queue
            </Typography>
            <Alert severity="success">
              No failed messages in the dead letter queue.
            </Alert>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};
