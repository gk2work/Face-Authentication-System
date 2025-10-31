import {
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Box,
  CircularProgress,
  IconButton,
} from '@mui/material';
import { Visibility as ViewIcon } from '@mui/icons-material';
import type { RecentApplication } from '@/types';

interface RecentApplicationsTableProps {
  applications: RecentApplication[];
  loading?: boolean;
  onViewDetails?: (applicationId: string) => void;
}

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

export const RecentApplicationsTable = ({
  applications,
  loading,
  onViewDetails,
}: RecentApplicationsTableProps) => {
  if (loading) {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Recent Applications
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

  if (!applications || applications.length === 0) {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Recent Applications
          </Typography>
          <Box
            sx={{
              height: 200,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Typography color="text.secondary">No recent applications</Typography>
          </Box>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Recent Applications
        </Typography>
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
                  sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
                >
                  <TableCell>
                    <Typography variant="body2" fontFamily="monospace">
                      {app.application_id.substring(0, 8)}...
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
                        {app.identity_id.substring(0, 8)}...
                      </Typography>
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        -
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    {app.is_duplicate !== undefined ? (
                      <Chip
                        label={app.is_duplicate ? 'Yes' : 'No'}
                        color={app.is_duplicate ? 'warning' : 'default'}
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
                  <TableCell align="right">
                    <IconButton
                      size="small"
                      onClick={() => onViewDetails?.(app.application_id)}
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
      </CardContent>
    </Card>
  );
};
