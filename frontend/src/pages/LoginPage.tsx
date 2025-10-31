import { useState } from 'react';
import type { FormEvent } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { authService } from '@/services';
import {
  Box,
  Button,
  Card,
  CardContent,
  TextField,
  Typography,
  Alert,
  CircularProgress,
  Container,
} from '@mui/material';
import { LockOutlined } from '@mui/icons-material';

interface LoginFormData {
  username: string;
  password: string;
}

interface LoginFormErrors {
  username?: string;
  password?: string;
}

export const LoginPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [formData, setFormData] = useState<LoginFormData>({
    username: '',
    password: '',
  });
  const [errors, setErrors] = useState<LoginFormErrors>({});
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string>('');

  const validateForm = (): boolean => {
    const newErrors: LoginFormErrors = {};

    if (!formData.username.trim()) {
      newErrors.username = 'Username is required';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleInputChange = (field: keyof LoginFormData) => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    setFormData({
      ...formData,
      [field]: event.target.value,
    });
    // Clear error for this field when user starts typing
    if (errors[field]) {
      setErrors({
        ...errors,
        [field]: undefined,
      });
    }
    // Clear general error message
    if (errorMessage) {
      setErrorMessage('');
    }
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsLoading(true);
    setErrorMessage('');

    try {
      await authService.login(formData);
      
      // Get the redirect location from state, or default to dashboard
      const from = (location.state as any)?.from?.pathname || '/dashboard';
      navigate(from, { replace: true });
    } catch (error: any) {
      setErrorMessage(
        error.response?.data?.message || 
        'Invalid credentials. Please try again.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Container maxWidth="sm">
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Card sx={{ width: '100%', maxWidth: 450 }}>
          <CardContent sx={{ p: 4 }}>
            <Box
              sx={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                mb: 3,
              }}
            >
              <Box
                sx={{
                  width: 56,
                  height: 56,
                  borderRadius: '50%',
                  bgcolor: 'primary.main',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  mb: 2,
                }}
              >
                <LockOutlined sx={{ color: 'white', fontSize: 32 }} />
              </Box>
              <Typography variant="h5" component="h1" fontWeight={600}>
                Sign In
              </Typography>
              <Typography variant="body2" color="text.secondary" mt={1}>
                Face Authentication System
              </Typography>
            </Box>

            {errorMessage && (
              <Alert severity="error" sx={{ mb: 3 }}>
                {errorMessage}
              </Alert>
            )}

            <form onSubmit={handleSubmit}>
              <TextField
                fullWidth
                label="Username"
                variant="outlined"
                value={formData.username}
                onChange={handleInputChange('username')}
                error={!!errors.username}
                helperText={errors.username}
                disabled={isLoading}
                autoComplete="username"
                autoFocus
                sx={{ mb: 2 }}
              />

              <TextField
                fullWidth
                label="Password"
                type="password"
                variant="outlined"
                value={formData.password}
                onChange={handleInputChange('password')}
                error={!!errors.password}
                helperText={errors.password}
                disabled={isLoading}
                autoComplete="current-password"
                sx={{ mb: 3 }}
              />

              <Button
                fullWidth
                type="submit"
                variant="contained"
                size="large"
                disabled={isLoading}
                sx={{ mb: 2 }}
              >
                {isLoading ? (
                  <CircularProgress size={24} color="inherit" />
                ) : (
                  'Sign In'
                )}
              </Button>
            </form>
          </CardContent>
        </Card>
      </Box>
    </Container>
  );
};
