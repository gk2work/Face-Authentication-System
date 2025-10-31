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
import { ProtectedRoute } from './components';
import { authService } from './services';

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/unauthorized" element={<UnauthorizedPage />} />

          {/* Protected routes */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/upload"
            element={
              <ProtectedRoute requiredRole="operator">
                <UploadPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/applications"
            element={
              <ProtectedRoute>
                <ApplicationListPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/applications/:id"
            element={
              <ProtectedRoute>
                <ApplicationDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/identities"
            element={
              <ProtectedRoute>
                <IdentityListPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/identities/:id"
            element={
              <ProtectedRoute>
                <IdentityDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin"
            element={
              <ProtectedRoute requiredRole="admin">
                <AdminPanelPage />
              </ProtectedRoute>
            }
          />

          {/* Default redirect */}
          <Route
            path="/"
            element={
              authService.isAuthenticated() ? (
                <Navigate to="/dashboard" replace />
              ) : (
                <Navigate to="/login" replace />
              )
            }
          />

          {/* Catch all - redirect to home */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
