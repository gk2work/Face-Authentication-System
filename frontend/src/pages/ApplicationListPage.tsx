import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Chip,
  IconButton,
  TextField,
  MenuItem,
  Alert,
  CircularProgress,
  InputAdornment,
} from '@mui/material';
import {
  Visibility as ViewIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
} from '@mui/icons-material';
import { DashboardLayout } from '@/components';
import { useApplications } from '@/hooks/useApplications';
import type { ApplicationFilters } from '@/types/application';

const statusOptions = [
  { value: '', label: 'All Statuses' },
  { value: 'pending', label: 'Pending' },
  { value: 'processing', label: 'Processing' },
  { value: 'completed', label: 'Completed' },
  { value: 'failed', label: 'Failed' },
];

const getStatusColor = (
  status: string
): 'default' | 'primary' | 'secondary' | 'error' | 'warning' | 'info' | 'success' => {
  switch (status) {
    case 'completed':
      return 'success';
    case 'processing':
      return 'info';
    case 'pending':
      return 'warning';
    case 'failed':
      return 'error';
    default:
      return 'default';
  }
};

export const ApplicationListPage = () => {
  const navigate = useNavigate();
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [filters, setFilters] = useState<ApplicationFilters>({});
  const [searchInput, setSearchInput] = useState('');

  const { applications, total, loading, error } = useApplications({
    page: page + 1,
    pageSize,
    filters,
  });

  const handleChangePage = (_event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setPageSize(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleStatusFilterChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setFilters({ ...filters, status: event.target.value || undefined });
    setPage(0);
  };

  const handleStartDateChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setFilters({ ...filters, start_date: event.target.value || undefined });
    setPage(0);
  };

  const handleEndDateChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setFilters({ ...filters, end_date: event.target.value || undefined });
    setPage(0);
  };

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchInput(event.target.value);
  };

  const handleSearchSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    setFilters({ ...filters, search: searchInput || undefined });
    setPage(0);
  };

  const handleViewDetails = (applicationId: string) => {
    navigate(`/applications/${applicationId}`);
  };

  return (
    <DashboardLayout>
      <Box>
        <Typography variant="h4" component="h1" gutterBottom>
          Applications
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
          View and manage all application submissions
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        <Paper sx={{ p: 3, mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
            <FilterIcon />
            <Typography variant="h6">Filters</Typography>
          </Box>

          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: {
                xs: '1fr',
                sm: 'repeat(2, 1fr)',
                md: 'repeat(4, 1fr)',
              },
              gap: 2,
            }}
          >
            <form onSubmit={handleSearchSubmit} style={{ display: 'contents' }}>
              <TextField
                label="Search Application ID"
                value={searchInput}
                onChange={handleSearchChange}
                size="small"
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton type="submit" edge="end" size="small">
                        <SearchIcon />
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />
            </form>

            <TextField
              select
              label="Status"
              value={filters.status || ''}
              onChange={handleStatusFilterChange}
              size="small"
            >
              {statusOptions.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </TextField>

            <TextField
              label="Start Date"
              type="date"
              value={filters.start_date || ''}
              onChange={handleStartDateChange}
              size="small"
              InputLabelProps={{ shrink: true }}
            />

            <TextField
              label="End Date"
              type="date"
              value={filters.end_date || ''}
              onChange={handleEndDateChange}
              size="small"
              InputLabelProps={{ shrink: true }}
            />
          </Box>
        </Paper>

        <Paper>
          {loading ? (
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                minHeight: 400,
              }}
            >
              <CircularProgress />
            </Box>
          ) : applications.length === 0 ? (
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                minHeight: 400,
              }}
            >
              <Typography color="text.secondary">No applications found</Typography>
            </Box>
          ) : (
            <>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Application ID</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Identity ID</TableCell>
                      <TableCell>Duplicate</TableCell>
                      <TableCell>Submitted</TableCell>
                      <TableCell align="right">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {applications.map((app) => (
                      <TableRow
                        key={app.application_id}
                        hover
                        sx={{ cursor: 'pointer' }}
                        onClick={() => handleViewDetails(app.application_id)}
                      >
                        <TableCell>
                          <Typography variant="body2" fontFamily="monospace">
                            {app.application_id.substring(0, 12)}...
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={app.status}
                            color={getStatusColor(app.status)}
                            size="small"
                            sx={{ textTransform: 'capitalize' }}
                          />
                        </TableCell>
                        <TableCell>
                          {app.identity_id ? (
                            <Typography variant="body2" fontFamily="monospace">
                              {app.identity_id.substring(0, 12)}...
                            </Typography>
                          ) : (
                            <Typography variant="body2" color="text.secondary">
                              -
                            </Typography>
                          )}
                        </TableCell>
                        <TableCell>
                          {app.processing_result?.is_duplicate !== undefined ? (
                            <Chip
                              label={app.processing_result.is_duplicate ? 'Yes' : 'No'}
                              color={app.processing_result.is_duplicate ? 'warning' : 'default'}
                              size="small"
                            />
                          ) : (
                            <Typography variant="body2" color="text.secondary">
                              -
                            </Typography>
                          )}
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {new Date(app.created_at).toLocaleString()}
                          </Typography>
                        </TableCell>
                        <TableCell align="right" onClick={(e) => e.stopPropagation()}>
                          <IconButton
                            size="small"
                            onClick={() => handleViewDetails(app.application_id)}
                            title="View details"
                          >
                            <ViewIcon fontSize="small" />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
              <TablePagination
                component="div"
                count={total}
                page={page}
                onPageChange={handleChangePage}
                rowsPerPage={pageSize}
                onRowsPerPageChange={handleChangeRowsPerPage}
                rowsPerPageOptions={[5, 10, 25, 50]}
              />
            </>
          )}
        </Paper>
      </Box>
    </DashboardLayout>
  );
};
