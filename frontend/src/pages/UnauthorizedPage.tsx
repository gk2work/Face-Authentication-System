import { Box, Container, Typography, Button } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { LockOutlined } from '@mui/icons-material';

export const UnauthorizedPage = () => {
  const navigate = useNavigate();

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
        <Box sx={{ textAlign: 'center' }}>
          <LockOutlined sx={{ fontSize: 80, color: 'error.main', mb: 2 }} />
          <Typography variant="h4" component="h1" gutterBottom>
            Access Denied
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            You don't have permission to access this page.
          </Typography>
          <Button variant="contained" onClick={() => navigate('/dashboard')}>
            Go to Dashboard
          </Button>
        </Box>
      </Box>
    </Container>
  );
};
