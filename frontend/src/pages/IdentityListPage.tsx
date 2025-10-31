import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  Card,
  CardContent,
  CardMedia,
  CardActionArea,
  Chip,
  TextField,
  MenuItem,
  Alert,
  CircularProgress,
  Pagination,
  InputAdornment,
  IconButton,
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  Person as PersonIcon,
} from '@mui/icons-material';
import { DashboardLayout } from '@/components';
import { useIdentities } from '@/hooks/useIdentities';
import type { IdentityFilters } from '@/types';

const statusOptions = [
  { value: '', label: 'All Statuses' },
  { value: 'active', label: 'Active' },
  { value: 'flagged', label: 'Flagged' },
  { value: 'merged', label: 'Merged' },
];

const getStatusColor = (
  status: string
): 'default' | 'primary' | 'secondary' | 'error' | 'warning' | 'info' | 'success' => {
  switch (status) {
    case 'active':
      return 'success';
    case 'flagged':
      return 'warning';
    case 'merged':
      return 'info';
    default:
      return 'default';
  }
};

export const IdentityListPage = () => {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<IdentityFilters>({});
  const [searchInput, setSearchInput] = useState('');

  const { identities, total, totalPages, loading, error } = useIdentities({
    page,
    pageSize: 12,
    filters,
  });

  const handlePageChange = (_event: React.ChangeEvent<unknown>, value: number) => {
    setPage(value);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleStatusFilterChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setFilters({ ...filters, status: event.target.value || undefined });
    setPage(1);
  };

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchInput(event.target.value);
  };

  const handleSearchSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    setFilters({ ...filters, search: searchInput || undefined });
    setPage(1);
  };

  const handleViewDetails = (identityId: string) => {
    navigate(`/identities/${identityId}`);
  };

  return (
    <DashboardLayout>
      <Box>
        <Typography variant="h4" component="h1" gutterBottom>
          Identities
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
          View and manage all unique identities in the system
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
              },
              gap: 2,
            }}
          >
            <form onSubmit={handleSearchSubmit}>
              <TextField
                fullWidth
                label="Search by Identity ID"
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
          </Box>
        </Paper>

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
        ) : identities.length === 0 ? (
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              minHeight: 400,
            }}
          >
            <Typography color="text.secondary">No identities found</Typography>
          </Box>
        ) : (
          <>
            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: {
                  xs: '1fr',
                  sm: 'repeat(2, 1fr)',
                  md: 'repeat(3, 1fr)',
                  lg: 'repeat(4, 1fr)',
                },
                gap: 3,
                mb: 4,
              }}
            >
              {identities.map((identity) => (
                <Card key={identity.unique_id}>
                  <CardActionArea onClick={() => handleViewDetails(identity.unique_id)}>
                    {identity.photographs && identity.photographs.length > 0 ? (
                      <CardMedia
                        component="img"
                        height="200"
                        image={identity.photographs[0]}
                        alt="Identity"
                        sx={{ objectFit: 'cover' }}
                      />
                    ) : (
                      <Box
                        sx={{
                          height: 200,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          bgcolor: 'action.hover',
                        }}
                      >
                        <PersonIcon sx={{ fontSize: 80, color: 'text.secondary' }} />
                      </Box>
                    )}
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                        <Typography variant="body2" color="text.secondary">
                          Identity ID
                        </Typography>
                        <Chip
                          label={identity.status}
                          color={getStatusColor(identity.status)}
                          size="small"
                          sx={{ textTransform: 'capitalize' }}
                        />
                      </Box>
                      <Typography variant="body2" fontFamily="monospace" gutterBottom>
                        {identity.unique_id.substring(0, 16)}...
                      </Typography>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
                        <Typography variant="caption" color="text.secondary">
                          Photos: {identity.photographs?.length || 0}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Applications: {identity.application_count}
                        </Typography>
                      </Box>
                      <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
                        Created: {new Date(identity.created_at).toLocaleDateString()}
                      </Typography>
                    </CardContent>
                  </CardActionArea>
                </Card>
              ))}
            </Box>

            {totalPages > 1 && (
              <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
                <Pagination
                  count={totalPages}
                  page={page}
                  onChange={handlePageChange}
                  color="primary"
                  size="large"
                />
              </Box>
            )}

            <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', mt: 2 }}>
              Showing {identities.length} of {total} identities
            </Typography>
          </>
        )}
      </Box>
    </DashboardLayout>
  );
};
