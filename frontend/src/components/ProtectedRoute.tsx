import { Navigate, useLocation } from 'react-router-dom';
import { authService } from '@/services';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRole?: 'admin' | 'operator' | 'viewer' | 'reviewer';
}

export const ProtectedRoute = ({ children, requiredRole }: ProtectedRouteProps) => {
  const location = useLocation();
  const isAuthenticated = authService.isAuthenticated();

  if (!isAuthenticated) {
    // Redirect to login page, but save the attempted location
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check role if required
  if (requiredRole) {
    const currentUser = authService.getCurrentUser();
    
    if (!currentUser) {
      return <Navigate to="/login" state={{ from: location }} replace />;
    }

    // Check if user has the required role
    const hasRequiredRole = currentUser.roles?.includes(requiredRole as any) || 
                           currentUser.role === requiredRole;

    // Admin has access to everything
    const isAdmin = currentUser.roles?.includes('admin') || currentUser.role === 'admin';

    if (!hasRequiredRole && !isAdmin) {
      // User doesn't have sufficient permissions
      return <Navigate to="/unauthorized" replace />;
    }
  }

  return <>{children}</>;
};
