/**
 * AdminUserDetail component
 * Displays detailed information and statistics for a specific admin user
 */

import React from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Chip,
  Button,
  Alert,
  Skeleton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Divider,
} from '@mui/material';
import {
  Edit,
  PersonOff,
  ArrowBack,
  Email,
  Person,
  CalendarToday,
  Login,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAdminUserStats } from '../hooks';
import { AdminActivityChart } from './AdminActivityChart';
import { superadminApi } from '../services/api';

interface AdminUserDetailProps {
  username: string;
  onEdit?: (username: string) => void;
  onDeactivate?: (username: string) => void;
  onBack?: () => void;
}

export const AdminUserDetail: React.FC<AdminUserDetailProps> = ({
  username,
  onEdit,
  onDeactivate,
  onBack,
}) => {
  const navigate = useNavigate();
  const { data: stats, loading, error } = useAdminUserStats({ username });
  const [user, setUser] = React.useState<any>(null);
  const [userLoading, setUserLoading] = React.useState(true);
  const [userError, setUserError] = React.useState<Error | null>(null);

  // Fetch user details
  React.useEffect(() => {
    const fetchUser = async () => {
      try {
        setUserLoading(true);
        const userData = await superadminApi.getAdminUser(username);
        setUser(userData);
      } catch (err) {
        setUserError(err instanceof Error ? err : new Error('Failed to fetch user'));
      } finally {
        setUserLoading(false);
      }
    };

    fetchUser();
  }, [username]);

  const handleBack = () => {
    if (onBack) {
      onBack();
    } else {
      navigate('/superadmin');
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (error || userError) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          Failed to load user details: {error?.message || userError?.message}
        </Alert>
        <Button
          startIcon={<ArrowBack />}
          onClick={handleBack}
          sx={{ mt: 2 }}
        >
          Back to List
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header with Actions */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Button
          startIcon={<ArrowBack />}
          onClick={handleBack}
        >
          Back to List
        </Button>
        <Box sx={{ display: 'flex', gap: 1 }}>
          {onEdit && user?.is_active && (
            <Button
              variant="outlined"
              startIcon={<Edit />}
              onClick={() => onEdit(username)}
            >
              Edit User
            </Button>
          )}
          {onDeactivate && user?.is_active && (
            <Button
              variant="outlined"
              color="error"
              startIcon={<PersonOff />}
              onClick={() => onDeactivate(username)}
            >
              Deactivate
            </Button>
          )}
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* User Information Card */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                User Information
              </Typography>
              <Divider sx={{ mb: 2 }} />
              
              {userLoading ? (
                <Box>
                  {[1, 2, 3, 4, 5].map((i) => (
                    <Skeleton key={i} height={40} sx={{ mb: 1 }} />
                  ))}
                </Box>
              ) : user ? (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Person color="action" />
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Username
                      </Typography>
                      <Typography variant="body1" fontWeight={500}>
                        {user.username}
                      </Typography>
                    </Box>
                  </Box>

                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Email color="action" />
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Email
                      </Typography>
                      <Typography variant="body1">
                        {user.email}
                      </Typography>
                    </Box>
                  </Box>

                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Full Name
                    </Typography>
                    <Typography variant="body1">
                      {user.full_name}
                    </Typography>
                  </Box>

                  <Box>
                    <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 0.5 }}>
                      Roles
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                      {user.roles.map((role: string) => (
                        <Chip
                          key={role}
                          label={role}
                          size="small"
                          color={role === 'superadmin' ? 'error' : 'primary'}
                        />
                      ))}
                    </Box>
                  </Box>

                  <Box>
                    <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 0.5 }}>
                      Status
                    </Typography>
                    <Chip
                      label={user.is_active ? 'Active' : 'Inactive'}
                      size="small"
                      color={user.is_active ? 'success' : 'default'}
                    />
                  </Box>

                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <CalendarToday color="action" fontSize="small" />
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Created
                      </Typography>
                      <Typography variant="body2">
                        {formatDate(user.created_at)}
                      </Typography>
                    </Box>
                  </Box>

                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Login color="action" fontSize="small" />
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Last Login
                      </Typography>
                      <Typography variant="body2">
                        {formatDate(user.last_login)}
                      </Typography>
                    </Box>
                  </Box>
                </Box>
              ) : null}
            </CardContent>
          </Card>
        </Grid>

        {/* Application Statistics Card */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Application Statistics
              </Typography>
              <Divider sx={{ mb: 2 }} />
              
              {loading ? (
                <Box>
                  {[1, 2, 3, 4].map((i) => (
                    <Skeleton key={i} height={40} sx={{ mb: 1 }} />
                  ))}
                </Box>
              ) : stats ? (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Total Applications
                    </Typography>
                    <Typography variant="h4" fontWeight={600}>
                      {stats.total_applications}
                    </Typography>
                  </Box>

                  <Box>
                    <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
                      By Status
                    </Typography>
                    <Grid container spacing={1}>
                      {Object.entries(stats.applications_by_status).map(([status, count]) => (
                        <Grid item xs={6} key={status}>
                          <Paper variant="outlined" sx={{ p: 1 }}>
                            <Typography variant="caption" color="text.secondary">
                              {status.charAt(0).toUpperCase() + status.slice(1)}
                            </Typography>
                            <Typography variant="h6" fontWeight={500}>
                              {count}
                            </Typography>
                          </Paper>
                        </Grid>
                      ))}
                    </Grid>
                  </Box>

                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Total Overrides
                    </Typography>
                    <Typography variant="h5" fontWeight={600}>
                      {stats.total_overrides}
                    </Typography>
                  </Box>

                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Last 30 Days
                    </Typography>
                    <Typography variant="h5" fontWeight={600}>
                      {stats.last_30_days_total}
                    </Typography>
                  </Box>
                </Box>
              ) : null}
            </CardContent>
          </Card>
        </Grid>

        {/* Activity Chart */}
        <Grid item xs={12}>
          <AdminActivityChart
            username={username}
            title={`${username}'s Activity Timeline`}
          />
        </Grid>

        {/* Override Decisions Table */}
        {stats && stats.overrides_by_decision && Object.keys(stats.overrides_by_decision).length > 0 && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Override Decisions
                </Typography>
                <Divider sx={{ mb: 2 }} />
                
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Decision Type</TableCell>
                        <TableCell align="right">Count</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {Object.entries(stats.overrides_by_decision).map(([decision, count]) => (
                        <TableRow key={decision}>
                          <TableCell>
                            {decision.charAt(0).toUpperCase() + decision.slice(1)}
                          </TableCell>
                          <TableCell align="right">{count}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    </Box>
  );
};
