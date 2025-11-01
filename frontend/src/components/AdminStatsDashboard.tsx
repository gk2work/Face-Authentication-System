/**
 * AdminStatsDashboard component
 * Displays aggregate statistics for all admin users
 */

import React from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Alert,
  CircularProgress,
  Skeleton,
} from '@mui/material';
import {
  People,
  PersonAdd,
  PersonOff,
  Assignment,
} from '@mui/icons-material';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { useAggregateStats } from '../hooks';
import { StatCard } from './StatCard';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

export const AdminStatsDashboard: React.FC = () => {
  const { data, loading, error } = useAggregateStats();

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          Failed to load statistics: {error.message}
        </Alert>
      </Box>
    );
  }

  // Prepare data for pie chart
  const roleChartData = data
    ? Object.entries(data.users_by_role).map(([role, count]) => ({
        name: role.charAt(0).toUpperCase() + role.slice(1),
        value: count,
      }))
    : [];

  return (
    <Box sx={{ p: 3 }}>
      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          {loading ? (
            <Skeleton variant="rectangular" height={140} />
          ) : (
            <StatCard
              title="Total Admin Users"
              value={data?.total_admin_users || 0}
              icon={<People />}
              loading={loading}
            />
          )}
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          {loading ? (
            <Skeleton variant="rectangular" height={140} />
          ) : (
            <StatCard
              title="Active Users"
              value={data?.active_admin_users || 0}
              icon={<PersonAdd />}
              loading={loading}
            />
          )}
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          {loading ? (
            <Skeleton variant="rectangular" height={140} />
          ) : (
            <StatCard
              title="Inactive Users"
              value={data?.inactive_admin_users || 0}
              icon={<PersonOff />}
              loading={loading}
            />
          )}
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          {loading ? (
            <Skeleton variant="rectangular" height={140} />
          ) : (
            <StatCard
              title="Applications (30 Days)"
              value={data?.total_applications_last_30_days || 0}
              icon={<Assignment />}
              loading={loading}
            />
          )}
        </Grid>
      </Grid>

      {/* Charts and Tables */}
      <Grid container spacing={3}>
        {/* Users by Role Pie Chart */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Users by Role
              </Typography>
              {loading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                  <CircularProgress />
                </Box>
              ) : roleChartData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={roleChartData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) =>
                        `${name}: ${(percent * 100).toFixed(0)}%`
                      }
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {roleChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <Typography variant="body2" color="text.secondary" sx={{ py: 4, textAlign: 'center' }}>
                  No role data available
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Most Active Users Table */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Most Active Users (Top 5)
              </Typography>
              {loading ? (
                <Box sx={{ py: 2 }}>
                  {[1, 2, 3, 4, 5].map((i) => (
                    <Skeleton key={i} height={40} sx={{ mb: 1 }} />
                  ))}
                </Box>
              ) : data?.most_active_users && data.most_active_users.length > 0 ? (
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Username</TableCell>
                        <TableCell>Full Name</TableCell>
                        <TableCell align="right">Applications</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {data.most_active_users.map((user) => (
                        <TableRow key={user.username}>
                          <TableCell>{user.username}</TableCell>
                          <TableCell>{user.full_name}</TableCell>
                          <TableCell align="right">{user.application_count}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Typography variant="body2" color="text.secondary" sx={{ py: 4, textAlign: 'center' }}>
                  No activity data available
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};
