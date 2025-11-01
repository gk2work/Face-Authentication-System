import { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControlLabel,
  Checkbox,
  Alert,
  CircularProgress,
  Typography,
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
} from '@mui/icons-material';
import { api } from '@/services';
import type { User } from '@/types';

interface UserFormData {
  username: string;
  email: string;
  password: string;
  full_name: string;
  roles: Array<'admin' | 'reviewer' | 'auditor' | 'operator'>;
}

export const UserManagement = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [formData, setFormData] = useState<UserFormData>({
    username: '',
    email: '',
    password: '',
    full_name: '',
    roles: ['operator'],
  });

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.get<User[]>('/api/v1/users');
      setUsers(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch users');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (user?: User) => {
    if (user) {
      setEditingUser(user);
      setFormData({
        username: user.username,
        email: user.email,
        password: '',
        full_name: user.full_name,
        roles: user.roles,
      });
    } else {
      setEditingUser(null);
      setFormData({
        username: '',
        email: '',
        password: '',
        full_name: '',
        roles: ['operator'],
      });
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingUser(null);
  };

  const handleSubmit = async () => {
    try {
      setError(null);
      if (editingUser) {
        // Update user
        await api.put(`/api/v1/users/${editingUser.username}`, {
          email: formData.email,
          full_name: formData.full_name,
          roles: formData.roles,
        });
      } else {
        // Create user
        await api.post('/api/v1/users', formData);
      }
      handleCloseDialog();
      fetchUsers();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save user');
    }
  };

  const handleDeactivate = async (username: string) => {
    if (!confirm(`Are you sure you want to deactivate user ${username}?`)) {
      return;
    }

    try {
      setError(null);
      await api.delete(`/api/v1/users/${username}`);
      fetchUsers();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to deactivate user');
    }
  };

  const handleRoleToggle = (role: 'admin' | 'reviewer' | 'auditor' | 'operator') => {
    setFormData((prev) => ({
      ...prev,
      roles: prev.roles.includes(role)
        ? prev.roles.filter((r) => r !== role)
        : [...prev.roles, role],
    }));
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6">Users</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
        >
          Create User
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Username</TableCell>
              <TableCell>Full Name</TableCell>
              <TableCell>Email</TableCell>
              <TableCell>Roles</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Last Login</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {users.map((user) => (
              <TableRow key={user.username}>
                <TableCell>{user.username}</TableCell>
                <TableCell>{user.full_name}</TableCell>
                <TableCell>{user.email}</TableCell>
                <TableCell>
                  {user.roles.map((role) => (
                    <Chip key={role} label={role} size="small" sx={{ mr: 0.5 }} />
                  ))}
                </TableCell>
                <TableCell>
                  <Chip
                    label={user.is_active ? 'Active' : 'Inactive'}
                    color={user.is_active ? 'success' : 'default'}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  {user.last_login
                    ? new Date(user.last_login).toLocaleString()
                    : 'Never'}
                </TableCell>
                <TableCell align="right">
                  <IconButton
                    size="small"
                    onClick={() => handleOpenDialog(user)}
                    title="Edit user"
                  >
                    <EditIcon fontSize="small" />
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={() => handleDeactivate(user.username)}
                    disabled={!user.is_active}
                    title="Deactivate user"
                  >
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>{editingUser ? 'Edit User' : 'Create User'}</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label="Username"
              value={formData.username}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              disabled={!!editingUser}
              fullWidth
              required
            />
            <TextField
              label="Full Name"
              value={formData.full_name}
              onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
              fullWidth
              required
            />
            <TextField
              label="Email"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              fullWidth
              required
            />
            {!editingUser && (
              <TextField
                label="Password"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                fullWidth
                required
                helperText="Minimum 8 characters"
              />
            )}
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Roles
              </Typography>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={formData.roles.includes('admin')}
                    onChange={() => handleRoleToggle('admin')}
                  />
                }
                label="Admin"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={formData.roles.includes('reviewer')}
                    onChange={() => handleRoleToggle('reviewer')}
                  />
                }
                label="Reviewer"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={formData.roles.includes('auditor')}
                    onChange={() => handleRoleToggle('auditor')}
                  />
                }
                label="Auditor"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={formData.roles.includes('operator')}
                    onChange={() => handleRoleToggle('operator')}
                  />
                }
                label="Operator"
              />
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained">
            {editingUser ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
