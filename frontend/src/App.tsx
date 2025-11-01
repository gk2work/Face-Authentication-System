import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { theme } from './theme';
import './styles/global.css';
import {
  LoginPage,
  DashboardPage,
  UnauthorizedPage,
  UploadPage,
  ApplicationListPage,
  ApplicationDetailPage,
  IdentityListPage,
  IdentityDetailPage,
  AdminPanelPage,
} from './pages';
import { SuperadminPage } from './pages/SuperadminPage';
import { ProtectedRoute } from './components';
import ErrorBoundary from './components/ErrorBoundary';
import { OfflineIndicator } from './components/OfflineIndicator';
import { authService } from './services';

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <OfflineIndicator />
        <BrowserRouter>
          <Routes>
          {/* Public routes - No authentication required */}
          <Route path="/" element={<UploadPage />} />
          <Route path="/apply" element={<UploadPage />} />
          <Route path="/check-status/:id" element={<ApplicationDetailPage />} />
          
          {/* Admin/Staff authentication routes */}
          <Route path="/admin/login" element={<LoginPage />} />
          <Route path="/unauthorized" element={<UnauthorizedPage />} />

          {/* Protected Admin/Staff routes */}
          <Route
            path="/admin/dashboard"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/applications"
            element={
              <ProtectedRoute>
                <ApplicationListPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/applications/:id"
            element={
              <ProtectedRoute>
                <ApplicationDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/identities"
            element={
              <ProtectedRoute>
                <IdentityListPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/identities/:id"
            element={
              <ProtectedRoute>
                <IdentityDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/panel"
            element={
              <ProtectedRoute requiredRole="admin">
                <AdminPanelPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/superadmin"
            element={
              <ProtectedRoute requiredRole="superadmin">
                <SuperadminPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/superadmin/users/:username"
            element={
              <ProtectedRoute requiredRole="superadmin">
                <SuperadminPage />
              </ProtectedRoute>
            }
          />

          {/* Legacy redirects for backward compatibility */}
          <Route path="/login" element={<Navigate to="/admin/login" replace />} />
          <Route path="/dashboard" element={<Navigate to="/admin/dashboard" replace />} />
          <Route path="/upload" element={<Navigate to="/apply" replace />} />
          <Route path="/applications" element={<Navigate to="/admin/applications" replace />} />
          <Route path="/identities" element={<Navigate to="/admin/identities" replace />} />
          <Route path="/admin" element={<Navigate to="/admin/panel" replace />} />

          {/* Catch all - redirect to home */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
