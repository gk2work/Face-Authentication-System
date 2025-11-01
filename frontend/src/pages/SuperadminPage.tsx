/**
 * SuperadminPage component
 * Main page for superadmin user management with tab-based navigation
 */

import React, { useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Tabs,
  Tab,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Breadcrumbs,
  Link,
  Alert,
} from '@mui/material';
import { Add, Home } from '@mui/icons-material';
import { useNavigate, useParams } from 'react-router-dom';
import { DashboardLayout } from '../components/DashboardLayout';
import { AdminStatsDashboard } from '../components/AdminStatsDashboard';
import { AdminUserList } from '../components/AdminUserList';
import { AdminUserDetail } from '../components/AdminUserDetail';
import { AdminUserForm } from '../components/AdminUserForm';
import { superadminApi } from '../services/api';

type ViewState = 'list' | 'detail' | 'create' | 'edit';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`superadmin-tabpanel-${index}`}
      aria-labelledby={`superadmin-tab-${index}`}
    >
      {value === index && <Box>{children}</Box>}
    </div>
  );
};

export const SuperadminPage: React.FC = () => {
  const navigate = useNavigate();
  const { username } = useParams<{ username: string }>();
  
  const [tabValue, setTabValue] = useState(0);
  const [viewState, setViewState] = useState<ViewState>(username ? 'detail' : 'list');
  const [selectedUsername, setSelectedUsername] = useState<string | undefined>(username);
  const [formDialogOpen, setFormDialogOpen] = useState(false);
  const [formMode, setFormMode] = useState<'create' | 'edit'>('create');
  const [deactivateDialogOpen, setDeactivateDialogOpen] = useState(false);
  const [userToDeactivate, setUserToDeactivate] = useState<string | null>(null);
  const [deactivateLoading, setDeactivateLoading] = useState(false);
  const [deactivateError, setDeactivateError] = useState<string | null>(null);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
    if (newValue === 1) {
      setViewState('list');
      setSelectedUsername(undefined);
      navigate('/superadmin');
    }
  };

  const handleViewUser = (username: string) => {
    setSelectedUsername(username);
    setViewState('detail');
    navigate(`/superadmin/users/${username}`);
  };

  const handleEditUser = (username: string) => {
    setSelectedUsername(username);
    setFormMode('edit');
    setFormDialogOpen(true);
  };

  const handleCreateUser = () => {
    setFormMode('create');
    setSelectedUsername(undefined);
    setFormDialogOpen(true);
  };

  const handleDeactivateUser = (username: string) => {
    setUserToDeactivate(username);
    setDeactivateDialogOpen(true);
    setDeactivateError(null);
  };

  const handleConfirmDeactivate = async () => {
    if (!userToDeactivate) return;

    setDeactivateLoading(true);
    setDeactivateError(null);

    try {
      await superadminApi.deactivateAdminUser(userToDeactivate);
      setDeactivateDialogOpen(false);
      setUserToDeactivate(null);
      
      // Refresh the view
      if (viewState === 'detail' && selectedUsername === userToDeactivate) {
        setViewState('list');
        setSelectedUsername(undefined);
        navigate('/superadmin');
      }
      
      // Switch to user management tab to see updated list
      setTabValue(1);
    } catch (err: any) {
      setDeactivateError(
        err.response?.data?.detail || err.message || 'Failed to deactivate user'
      );
    } finally {
      setDeactivateLoading(false);
    }
  };

  const handleCancelDeactivate = () => {
    setDeactivateDialogOpen(false);
    setUserToDeactivate(null);
    setDeactivateError(null);
  };

  const handleFormSuccess = () => {
    setFormDialogOpen(false);
    setSelectedUsername(undefined);
    
    // Switch to user management tab to see updated list
    setTabValue(1);
    setViewState('list');
  };

  const handleFormCancel = () => {
    setFormDialogOpen(false);
    setSelectedUsername(undefined);
  };

  const handleBackToList = () => {
    setViewState('list');
    setSelectedUsername(undefined);
    navigate('/superadmin');
  };

  return (
    <DashboardLayout>
      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        {/* Breadcrumbs */}
        <Breadcrumbs sx={{ mb: 2 }}>
          <Link
            color="inherit"
            href="/"
            onClick={(e) => {
              e.preventDefault();
              navigate('/');
            }}
            sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}
          >
            <Home fontSize="small" />
            Dashboard
          </Link>
          <Typography color="text.primary">Superadmin</Typography>
          {viewState === 'detail' && selectedUsername && (
            <Typography color="text.primary">{selectedUsername}</Typography>
          )}
        </Breadcrumbs>

        {/* Page Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Box>
            <Typography variant="h4" component="h1" gutterBottom>
              Superadmin Management
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Manage admin users, view statistics, and monitor activity
            </Typography>
          </Box>
          {tabValue === 1 && viewState === 'list' && (
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={handleCreateUser}
            >
              Create User
            </Button>
          )}
        </Box>

        {/* Tabs */}
        {viewState !== 'detail' && (
          <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
            <Tabs value={tabValue} onChange={handleTabChange} aria-label="superadmin tabs">
              <Tab label="Overview" id="superadmin-tab-0" aria-controls="superadmin-tabpanel-0" />
              <Tab label="User Management" id="superadmin-tab-1" aria-controls="superadmin-tabpanel-1" />
            </Tabs>
          </Box>
        )}

        {/* Tab Panels */}
        {viewState !== 'detail' && (
          <>
            <TabPanel value={tabValue} index={0}>
              <AdminStatsDashboard />
            </TabPanel>

            <TabPanel value={tabValue} index={1}>
              <AdminUserList
                onViewUser={handleViewUser}
                onEditUser={handleEditUser}
                onDeactivateUser={handleDeactivateUser}
              />
            </TabPanel>
          </>
        )}

        {/* Detail View */}
        {viewState === 'detail' && selectedUsername && (
          <AdminUserDetail
            username={selectedUsername}
            onEdit={handleEditUser}
            onDeactivate={handleDeactivateUser}
            onBack={handleBackToList}
          />
        )}

        {/* Create/Edit User Dialog */}
        <Dialog
          open={formDialogOpen}
          onClose={handleFormCancel}
          maxWidth="md"
          fullWidth
        >
          <DialogTitle>
            {formMode === 'create' ? 'Create New Admin User' : `Edit User: ${selectedUsername}`}
          </DialogTitle>
          <DialogContent>
            <Box sx={{ pt: 2 }}>
              <AdminUserForm
                mode={formMode}
                username={selectedUsername}
                onSuccess={handleFormSuccess}
                onCancel={handleFormCancel}
              />
            </Box>
          </DialogContent>
        </Dialog>

        {/* Deactivate Confirmation Dialog */}
        <Dialog
          open={deactivateDialogOpen}
          onClose={handleCancelDeactivate}
          maxWidth="sm"
          fullWidth
        >
          <DialogTitle>Confirm Deactivation</DialogTitle>
          <DialogContent>
            {deactivateError && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {deactivateError}
              </Alert>
            )}
            <Typography>
              Are you sure you want to deactivate user <strong>{userToDeactivate}</strong>?
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              The user will no longer be able to log in or access the system.
            </Typography>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCancelDeactivate} disabled={deactivateLoading}>
              Cancel
            </Button>
            <Button
              onClick={handleConfirmDeactivate}
              color="error"
              variant="contained"
              disabled={deactivateLoading}
            >
              {deactivateLoading ? 'Deactivating...' : 'Deactivate'}
            </Button>
          </DialogActions>
        </Dialog>
      </Container>
    </DashboardLayout>
  );
};
