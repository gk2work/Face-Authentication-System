import { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  TextField,
  Button,
  Grid,
  Chip,
  IconButton,
  Collapse,
  Typography,
  Alert,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import {
  KeyboardArrowDown as KeyboardArrowDownIcon,
  KeyboardArrowUp as KeyboardArrowUpIcon,
  Download as DownloadIcon,
  Search as SearchIcon,
} from '@mui/icons-material';
import { api } from '@/services';

interface AuditLog {
  event_type: string;
  timestamp: string;
  actor_id: string;
  actor_type: string;
  resource_id?: string;
  resource_type?: string;
  action: string;
  details: Record<string, any>;
  ip_address?: string;
  success: boolean;
  error_message?: string;
}

interface AuditLogsResponse {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  logs: AuditLog[];
}

interface AuditLogRowProps {
  log: AuditLog;
}

function AuditLogRow({ log }: AuditLogRowProps) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <TableRow sx={{ '& > *': { borderBottom: 'unset' } }}>
        <TableCell>
          <IconButton size="small" onClick={() => setOpen(!open)}>
            {open ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
          </IconButton>
        </TableCell>
        <TableCell>{new Date(log.timestamp).toLocaleString()}</TableCell>
        <TableCell>
          <Chip label={log.event_type} size="small" />
        </TableCell>
        <TableCell>{log.actor_id}</TableCell>
        <TableCell>{log.action}</TableCell>
        <TableCell>
          <Chip
            label={log.success ? 'Success' : 'Failed'}
            color={log.success ? 'success' : 'error'}
            size="small"
          />
        </TableCell>
      </TableRow>
      <TableRow>
        <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={6}>
          <Collapse in={open} timeout="auto" unmountOnExit>
            <Box sx={{ margin: 2 }}>
              <Typography variant="h6" gutterBottom component="div">
                Details
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Actor Type: {log.actor_type}
                  </Typography>
                  {log.resource_id && (
                    <Typography variant="body2" color="text.secondary">
                      Resource ID: {log.resource_id}
                    </Typography>
                  )}
                  {log.resource_type && (
                    <Typography variant="body2" color="text.secondary">
                      Resource Type: {log.resource_type}
                    </Typography>
                  )}
                  {log.ip_address && (
                    <Typography variant="body2" color="text.secondary">
                      IP Address: {log.ip_address}
                    </Typography>
                  )}
                </Grid>
                <Grid item xs={12} sm={6}>
                  {log.error_message && (
                    <Alert severity="error" sx={{ mb: 1 }}>
                      {log.error_message}
                    </Alert>
                  )}
                  {Object.keys(log.details).length > 0 && (
                    <Box>
                      <Typography variant="subtitle2" gutterBottom>
                        Additional Details:
                      </Typography>
                      <Paper variant="outlined" sx={{ p: 1, bgcolor: 'grey.50' }}>
                        <pre style={{ margin: 0, fontSize: '0.75rem', overflow: 'auto' }}>
                          {JSON.stringify(log.details, null, 2)}
                        </pre>
                      </Paper>
                    </Box>
                  )}
                </Grid>
              </Grid>
            </Box>
          </Collapse>
        </TableCell>
      </TableRow>
    </>
  );
}

export const AuditLogViewer = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [total, setTotal] = useState(0);
  
  // Filters
  const [eventType, setEventType] = useState('');
  const [actorId, setActorId] = useState('');
  const [resourceId, setResourceId] = useState('');

  useEffect(() => {
    fetchLogs();
  }, [page, rowsPerPage]);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const params = new URLSearchParams({
        page: String(page + 1),
        page_size: String(rowsPerPage),
      });
      
      if (eventType) params.append('event_type', eventType);
      if (actorId) params.append('actor_id', actorId);
      if (resourceId) params.append('resource_id', resourceId);
      
      const data = await api.get<AuditLogsResponse>(
        `/api/v1/admin/audit-logs?${params.toString()}`
      );
      
      setLogs(data.logs);
      setTotal(data.total);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch audit logs');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    setPage(0);
    fetchLogs();
  };

  const handleExport = async () => {
    try {
      const params = new URLSearchParams();
      if (eventType) params.append('event_type', eventType);
      if (actorId) params.append('actor_id', actorId);
      if (resourceId) params.append('resource_id', resourceId);
      
      const response = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/api/v1/admin/audit-logs/export?${params.toString()}`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },
        }
      );
      
      if (!response.ok) {
        throw new Error('Export failed');
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `audit_logs_${new Date().toISOString()}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      setError('Failed to export audit logs');
    }
  };

  const handleChangePage = (_event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  return (
    <Box>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6">Audit Logs</Typography>
        <Button
          variant="outlined"
          startIcon={<DownloadIcon />}
          onClick={handleExport}
        >
          Export CSV
        </Button>
      </Box>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Event Type</InputLabel>
              <Select
                value={eventType}
                label="Event Type"
                onChange={(e) => setEventType(e.target.value)}
              >
                <MenuItem value="">All</MenuItem>
                <MenuItem value="application_submitted">Application Submitted</MenuItem>
                <MenuItem value="face_detected">Face Detected</MenuItem>
                <MenuItem value="duplicate_detected">Duplicate Detected</MenuItem>
                <MenuItem value="manual_override">Manual Override</MenuItem>
                <MenuItem value="admin_login">Admin Login</MenuItem>
                <MenuItem value="data_modification">Data Modification</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={3}>
            <TextField
              fullWidth
              size="small"
              label="Actor ID"
              value={actorId}
              onChange={(e) => setActorId(e.target.value)}
            />
          </Grid>
          <Grid item xs={12} sm={3}>
            <TextField
              fullWidth
              size="small"
              label="Resource ID"
              value={resourceId}
              onChange={(e) => setResourceId(e.target.value)}
            />
          </Grid>
          <Grid item xs={12} sm={3}>
            <Button
              fullWidth
              variant="contained"
              startIcon={<SearchIcon />}
              onClick={handleSearch}
            >
              Search
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {loading ? (
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress />
        </Box>
      ) : (
        <>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell />
                  <TableCell>Timestamp</TableCell>
                  <TableCell>Event Type</TableCell>
                  <TableCell>Actor</TableCell>
                  <TableCell>Action</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {logs.map((log, index) => (
                  <AuditLogRow key={`${log.timestamp}-${index}`} log={log} />
                ))}
              </TableBody>
            </Table>
          </TableContainer>
          <TablePagination
            rowsPerPageOptions={[10, 25, 50, 100]}
            component="div"
            count={total}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={handleChangePage}
            onRowsPerPageChange={handleChangeRowsPerPage}
          />
        </>
      )}
    </Box>
  );
};
