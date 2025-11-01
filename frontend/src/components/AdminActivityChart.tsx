/**
 * AdminActivityChart component
 * Displays a line chart of admin activity over time
 */

import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  ToggleButton,
  ToggleButtonGroup,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { useAdminActivity } from '../hooks';

interface AdminActivityChartProps {
  username?: string;
  title?: string;
}

export const AdminActivityChart: React.FC<AdminActivityChartProps> = ({
  username,
  title = 'Activity Timeline',
}) => {
  const [dateRange, setDateRange] = useState<number>(30);

  const { data, loading, error } = useAdminActivity({
    username,
    autoFetch: true,
  });

  const handleDateRangeChange = (
    _event: React.MouseEvent<HTMLElement>,
    newRange: number | null
  ) => {
    if (newRange !== null) {
      setDateRange(newRange);
    }
  };

  // Filter data based on selected date range
  const filteredData = data
    ? data.slice(-dateRange)
    : [];

  if (error) {
    return (
      <Card>
        <CardContent>
          <Alert severity="error">
            Failed to load activity data: {error.message}
          </Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">
            {title}
          </Typography>
          <ToggleButtonGroup
            value={dateRange}
            exclusive
            onChange={handleDateRangeChange}
            size="small"
            aria-label="date range"
          >
            <ToggleButton value={7} aria-label="7 days">
              7 Days
            </ToggleButton>
            <ToggleButton value={14} aria-label="14 days">
              14 Days
            </ToggleButton>
            <ToggleButton value={30} aria-label="30 days">
              30 Days
            </ToggleButton>
          </ToggleButtonGroup>
        </Box>

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
            <CircularProgress />
          </Box>
        ) : filteredData.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart
              data={filteredData}
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 12 }}
                tickFormatter={(value) => {
                  const date = new Date(value);
                  return `${date.getMonth() + 1}/${date.getDate()}`;
                }}
              />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip
                labelFormatter={(value) => {
                  const date = new Date(value);
                  return date.toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    year: 'numeric',
                  });
                }}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="applications_processed"
                stroke="#8884d8"
                name="Total Processed"
                strokeWidth={2}
              />
              <Line
                type="monotone"
                dataKey="verified"
                stroke="#82ca9d"
                name="Verified"
                strokeWidth={2}
              />
              <Line
                type="monotone"
                dataKey="duplicate"
                stroke="#ffc658"
                name="Duplicate"
                strokeWidth={2}
              />
              <Line
                type="monotone"
                dataKey="rejected"
                stroke="#ff8042"
                name="Rejected"
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <Box sx={{ py: 8, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              No activity data available for the selected period
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};
