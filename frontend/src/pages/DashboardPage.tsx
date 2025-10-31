import { Box, Typography, Alert } from '@mui/material';
import {
  Description as ApplicationIcon,
  People as IdentityIcon,
  ContentCopy as DuplicateIcon,
  PendingActions as PendingIcon,
} from '@mui/icons-material';
import { DashboardLayout, StatCard, ApplicationTimelineChart, RecentApplicationsTable, SystemHealthIndicator } from '@/components';
import { useDashboardStats, useApplicationTimeline, useRecentApplications, useSystemHealth } from '@/hooks';
import { useNavigate } from 'react-router-dom';

export const DashboardPage = () => {
  const navigate = useNavigate();
  const { stats, loading, error } = useDashboardStats(true, 30000);
  const { data: timelineData, loading: timelineLoading } = useApplicationTimeline(30);
  const { applications, loading: applicationsLoading } = useRecentApplications(10);
  const { health, loading: healthLoading } = useSystemHealth(true, 30000);

  const handleViewDetails = (applicationId: string) => {
    navigate(`/applications/${applicationId}`);
  };

  return (
    <DashboardLayout>
      <Box>
        <Typography variant="h4" component="h1" gutterBottom>
          Dashboard Overview
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
          Monitor system performance and recent activity
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: {
              xs: '1fr',
              sm: 'repeat(2, 1fr)',
              md: 'repeat(4, 1fr)',
            },
            gap: 3,
          }}
        >
          <StatCard
            title="Total Applications"
            value={stats?.total_applications || 0}
            icon={<ApplicationIcon sx={{ fontSize: 32 }} />}
            trend={
              stats?.applications_trend
                ? {
                    value: stats.applications_trend,
                    isPositive: stats.applications_trend > 0,
                  }
                : undefined
            }
            loading={loading}
          />

          <StatCard
            title="Total Identities"
            value={stats?.total_identities || 0}
            icon={<IdentityIcon sx={{ fontSize: 32 }} />}
            trend={
              stats?.identities_trend
                ? {
                    value: stats.identities_trend,
                    isPositive: stats.identities_trend > 0,
                  }
                : undefined
            }
            loading={loading}
          />

          <StatCard
            title="Duplicates Detected"
            value={stats?.total_duplicates || 0}
            icon={<DuplicateIcon sx={{ fontSize: 32 }} />}
            trend={
              stats?.duplicates_trend
                ? {
                    value: stats.duplicates_trend,
                    isPositive: false,
                  }
                : undefined
            }
            loading={loading}
          />

          <StatCard
            title="Pending Applications"
            value={stats?.pending_applications || 0}
            icon={<PendingIcon sx={{ fontSize: 32 }} />}
            loading={loading}
          />
        </Box>

        <Box sx={{ mt: 4 }}>
          <ApplicationTimelineChart data={timelineData} loading={timelineLoading} />
        </Box>

        <Box sx={{ mt: 4 }}>
          <RecentApplicationsTable
            applications={applications}
            loading={applicationsLoading}
            onViewDetails={handleViewDetails}
          />
        </Box>

        <Box sx={{ mt: 4 }}>
          <SystemHealthIndicator health={health} loading={healthLoading} />
        </Box>
      </Box>
    </DashboardLayout>
  );
};
