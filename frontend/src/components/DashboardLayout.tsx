import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  List,
  Typography,
  Divider,
  IconButton,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Avatar,
  Menu,
  MenuItem,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  CloudUpload as UploadIcon,
  Description as ApplicationIcon,
  People as IdentityIcon,
  AdminPanelSettings as AdminIcon,
  AccountCircle,
  Logout,
} from '@mui/icons-material';
import { authService } from '@/services';

const drawerWidth = 240;

interface DashboardLayoutProps {
  children: React.ReactNode;
}

interface NavItem {
  text: string;
  icon: React.ReactElement;
  path: string;
  requiredRole?: 'admin' | 'operator' | 'viewer' | 'reviewer';
}

const navItems: NavItem[] = [
  { text: 'Dashboard', icon: <DashboardIcon />, path: '/dashboard' },
  { text: 'Upload', icon: <UploadIcon />, path: '/upload', requiredRole: 'operator' },
  { text: 'Applications', icon: <ApplicationIcon />, path: '/applications' },
  { text: 'Identities', icon: <IdentityIcon />, path: '/identities' },
  { text: 'Admin Panel', icon: <AdminIcon />, path: '/admin', requiredRole: 'admin' },
];

export const DashboardLayout = ({ children }: DashboardLayoutProps) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const currentUser = authService.getCurrentUser();

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    handleMenuClose();
    authService.logout();
  };

  const handleNavigation = (path: string) => {
    navigate(path);
    setMobileOpen(false);
  };

  const canAccessRoute = (item: NavItem): boolean => {
    if (!item.requiredRole || !currentUser) {
      return true;
    }

    // Check if user has the required role
    const hasRequiredRole = currentUser.roles?.includes(item.requiredRole as any) || 
                           currentUser.role === item.requiredRole;

    // Admin has access to everything
    const isAdmin = currentUser.roles?.includes('admin') || currentUser.role === 'admin';

    return hasRequiredRole || isAdmin;
  };

  const drawer = (
    <Box>
      <Toolbar>
        <Typography variant="h6" noWrap component="div">
          Face Auth System
        </Typography>
      </Toolbar>
      <Divider />
      <List>
        {navItems.filter(canAccessRoute).map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => handleNavigation(item.path)}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar
        position="fixed"
        sx={{
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: { sm: `${drawerWidth}px` },
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            {navItems.find((item) => item.path === location.pathname)?.text || 'Dashboard'}
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="body2" sx={{ display: { xs: 'none', sm: 'block' } }}>
              {currentUser?.username || 'User'}
            </Typography>
            <IconButton onClick={handleMenuOpen} color="inherit">
              <Avatar sx={{ width: 32, height: 32, bgcolor: 'secondary.main' }}>
                <AccountCircle />
              </Avatar>
            </IconButton>
          </Box>
        </Toolbar>
      </AppBar>

      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'right',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
      >
        <MenuItem disabled>
          <Typography variant="body2" color="text.secondary">
            Role: {currentUser?.roles?.join(', ') || currentUser?.role || 'Unknown'}
          </Typography>
        </MenuItem>
        <Divider />
        <MenuItem onClick={handleLogout}>
          <ListItemIcon>
            <Logout fontSize="small" />
          </ListItemIcon>
          Logout
        </MenuItem>
      </Menu>

      <Box
        component="nav"
        sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
      >
        {/* Mobile drawer */}
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true, // Better mobile performance
          }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
        >
          {drawer}
        </Drawer>

        {/* Desktop drawer */}
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          minHeight: '100vh',
          bgcolor: 'background.default',
        }}
      >
        <Toolbar />
        {children}
      </Box>
    </Box>
  );
};
