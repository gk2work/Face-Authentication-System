import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  CircularProgress,
} from '@mui/material';
import {
  CheckCircle as HealthyIcon,
  Warning as DegradedIcon,
  Error as DownIcon,
  Storage as DatabaseIcon,
  Face as FaceRecognitionIcon,
  CloudQueue as StorageIcon,
} from '@mui/icons-material';
import type { SystemHealth } from '@/types';

interface SystemHealthIndicatorProps {
  health: SystemHealth | null;
  loading?: boolean;
}

type HealthStatus = 'healthy' | 'degraded' | 'down';

const getStatusColor = (
  status: HealthStatus
): 'success' | 'warning' | 'error' => {
  switch (status) {
    case 'healthy':
      return 'success';
    case 'degraded':
      return 'warning';
    case 'down':
      return 'error';
  }
};

const getStatusIcon = (status: HealthStatus) => {
  switch (status) {
    case 'healthy':
      return <HealthyIcon fontSize="small" />;
    case 'degraded':
      return <DegradedIcon fontSize="small" />;
    case 'down':
      return <DownIcon fontSize="small" />;
  }
};

interface ServiceStatusProps {
  name: string;
  status: HealthStatus;
  icon: React.ReactElement;
}

const ServiceStatus = ({ name, status, icon }: ServiceStatusProps) => {
  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        p: 2,
        borderRadius: 1,
        bgcolor: 'background.paper',
        border: '1px solid',
        borderColor: 'divider',
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
        <Box
          sx={{
            width: 40,
            height: 40,
            borderRadius: 1,
            bgcolor: `${getStatusColor(status)}.light`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: `${getStatusColor(status)}.main`,
          }}
        >
          {icon}
        </Box>
        <Typography variant="body1" fontWeight={500}>
          {name}
        </Typography>
      </Box>
      <Chip
        icon={getStatusIcon(status)}
        label={status}
        color={getStatusColor(status)}
        size="small"
        sx={{ textTransform: 'capitalize' }}
      />
    </Box>
  );
};

export const SystemHealthIndicator = ({ health, loading }: SystemHealthIndicatorProps) => {
  if (loading) {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            System Health
          </Typography>
          <Box
            sx={{
              height: 200,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <CircularProgress />
          </Box>
        </CardContent>
      </Card>
    );
  }

  if (!health) {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            System Health
          </Typography>
          <Box
            sx={{
              height: 200,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Typography color="text.secondary">Health data unavailable</Typography>
          </Box>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h6">System Health</Typography>
          <Typography variant="caption" color="text.secondary">
            Last checked: {new Date(health.last_check).toLocaleTimeString()}
          </Typography>
        </Box>

        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: {
              xs: '1fr',
              md: 'repeat(3, 1fr)',
            },
            gap: 2,
          }}
        >
          <ServiceStatus
            name="Database"
            status={health.database_status}
            icon={<DatabaseIcon />}
          />
          <ServiceStatus
            name="Face Recognition"
            status={health.face_recognition_service}
            icon={<FaceRecognitionIcon />}
          />
          <ServiceStatus
            name="Storage"
            status={health.storage_service}
            icon={<StorageIcon />}
          />
        </Box>
      </CardContent>
    </Card>
  );
};
