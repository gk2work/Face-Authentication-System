import { useState } from 'react';
import { Box, Tabs, Tab, Typography, Paper } from '@mui/material';
import { DashboardLayout } from '@/components';
import { UserManagement } from '@/components/UserManagement';
import { SystemHealthDashboard } from '@/components/SystemHealthDashboard';
import { AuditLogViewer } from '@/components/AuditLogViewer';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`admin-tabpanel-${index}`}
      aria-labelledby={`admin-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

export const AdminPanelPage = () => {
  const [currentTab, setCurrentTab] = useState(0);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  return (
    <DashboardLayout>
      <Box>
        <Typography variant="h4" gutterBottom>
          Admin Panel
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Manage users, monitor system health, and view audit logs
        </Typography>

        <Paper sx={{ width: '100%' }}>
          <Tabs
            value={currentTab}
            onChange={handleTabChange}
            aria-label="admin panel tabs"
            sx={{ borderBottom: 1, borderColor: 'divider' }}
          >
            <Tab label="User Management" id="admin-tab-0" />
            <Tab label="System Health" id="admin-tab-1" />
            <Tab label="Audit Logs" id="admin-tab-2" />
          </Tabs>

          <TabPanel value={currentTab} index={0}>
            <UserManagement />
          </TabPanel>

          <TabPanel value={currentTab} index={1}>
            <SystemHealthDashboard />
          </TabPanel>

          <TabPanel value={currentTab} index={2}>
            <AuditLogViewer />
          </TabPanel>
        </Paper>
      </Box>
    </DashboardLayout>
  );
};
