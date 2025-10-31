import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  Chip,
  Button,
  Alert,
  CircularProgress,
  Divider,
  Card,
  CardContent,
  CardMedia,
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  CheckCircle as ApproveIcon,
  Cancel as RejectIcon,
} from '@mui/icons-material';
import { DashboardLayout } from '@/components';
import { api } from '@/services';
import type { Application } from '@/types/application';

const getStatusColor = (
  status: string
): 'default' | 'primary' | 'secondary' | 'error' | 'warning' | 'info' | 'success' => {
  switch (status) {
    case 'completed':
      return 'success';
    case 'processing':
      return 'info';
    case 'pending':
      return 'warning';
    case 'failed':
      return 'error';
    default:
      return 'default';
  }
};

export const ApplicationDetailPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [application, setApplication] = useState<Application | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    fetchApplication();
  }, [id]);

  const fetchApplication = async () => {
    if (!id) return;

    try {
      setLoading(true);
      setError(null);
      const data = await api.get<Application>(`/api/v1/applications/${id}`);
      setApplication(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch application details');
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmMatch = async () => {
    if (!id) return;

    try {
      setActionLoading(true);
      await api.post(`/api/v1/applications/${id}/confirm-match`);
      await fetchApplication();
    } catch (err: any) {
      setError(err.message || 'Failed to confirm match');
    } finally {
      setActionLoading(false);
    }
  };

  const handleRejectMatch = async () => {
    if (!id) return;

    try {
      setActionLoading(true);
      await api.post(`/api/v1/applications/${id}/reject-match`);
      await fetchApplication();
    } catch (err: any) {
      setError(err.message || 'Failed to reject match');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <DashboardLayout>
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            minHeight: 400,
          }}
        >
          <CircularProgress />
        </Box>
      </DashboardLayout>
    );
  }

  if (error || !application) {
    return (
      <DashboardLayout>
        <Box>
          <Button startIcon={<BackIcon />} onClick={() => navigate('/applications')} sx={{ mb: 3 }}>
            Back to Applications
          </Button>
          <Alert severity="error">{error || 'Application not found'}</Alert>
        </Box>
      </DashboardLayout>
    );
  }

  const showMatchActions =
    application.processing_result?.is_duplicate &&
    application.processing_result?.confidence_score &&
    application.processing_result.confidence_score >= 0.85 &&
    application.processing_result.confidence_score < 0.95;

  return (
    <DashboardLayout>
      <Box>
        <Button startIcon={<BackIcon />} onClick={() => navigate('/applications')} sx={{ mb: 3 }}>
          Back to Applications
        </Button>

        <Typography variant="h4" component="h1" gutterBottom>
          Application Details
        </Typography>

        <Paper sx={{ p: 3, mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h6">Basic Information</Typography>
            <Chip
              label={application.status}
              color={getStatusColor(application.status)}
              sx={{ textTransform: 'capitalize' }}
            />
          </Box>

          <Box sx={{ display: 'grid', gap: 2 }}>
            <Box>
              <Typography variant="body2" color="text.secondary">
                Application ID
              </Typography>
              <Typography variant="body1" fontFamily="monospace">
                {application.application_id}
              </Typography>
            </Box>

            {application.identity_id && (
              <Box>
                <Typography variant="body2" color="text.secondary">
                  Identity ID
                </Typography>
                <Typography variant="body1" fontFamily="monospace">
                  {application.identity_id}
                </Typography>
              </Box>
            )}

            <Box>
              <Typography variant="body2" color="text.secondary">
                Submitted
              </Typography>
              <Typography variant="body1">
                {new Date(application.created_at).toLocaleString()}
              </Typography>
            </Box>

            {application.metadata && (
              <Box>
                <Typography variant="body2" color="text.secondary">
                  Metadata
                </Typography>
                <Typography variant="body1">{application.metadata}</Typography>
              </Box>
            )}
          </Box>
        </Paper>

        {application.photograph_path && (
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Uploaded Photograph
            </Typography>
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'center',
                mt: 2,
              }}
            >
              <img
                src={application.photograph_path}
                alt="Application"
                style={{
                  maxWidth: '100%',
                  maxHeight: 400,
                  objectFit: 'contain',
                }}
              />
            </Box>
          </Paper>
        )}

        {application.processing_result && (
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Processing Results
            </Typography>

            <Box sx={{ display: 'grid', gap: 2, mt: 2 }}>
              <Box>
                <Typography variant="body2" color="text.secondary">
                  Face Detected
                </Typography>
                <Chip
                  label={application.processing_result.face_detected ? 'Yes' : 'No'}
                  color={application.processing_result.face_detected ? 'success' : 'error'}
                  size="small"
                />
              </Box>

              <Box>
                <Typography variant="body2" color="text.secondary">
                  Duplicate Status
                </Typography>
                <Chip
                  label={application.processing_result.is_duplicate ? 'Duplicate' : 'Unique'}
                  color={application.processing_result.is_duplicate ? 'warning' : 'success'}
                  size="small"
                />
              </Box>

              {application.processing_result.confidence_score !== undefined && (
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Confidence Score
                  </Typography>
                  <Typography variant="body1">
                    {(application.processing_result.confidence_score * 100).toFixed(2)}%
                  </Typography>
                </Box>
              )}

              {application.processing_result.quality_score !== undefined && (
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Image Quality Score
                  </Typography>
                  <Typography variant="body1">
                    {(application.processing_result.quality_score * 100).toFixed(2)}%
                  </Typography>
                </Box>
              )}
            </Box>

            {showMatchActions && (
              <Box sx={{ mt: 3 }}>
                <Divider sx={{ mb: 2 }} />
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  This match has medium confidence. Please review and confirm or reject.
                </Typography>
                <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
                  <Button
                    variant="contained"
                    color="success"
                    startIcon={<ApproveIcon />}
                    onClick={handleConfirmMatch}
                    disabled={actionLoading}
                  >
                    Confirm Match
                  </Button>
                  <Button
                    variant="outlined"
                    color="error"
                    startIcon={<RejectIcon />}
                    onClick={handleRejectMatch}
                    disabled={actionLoading}
                  >
                    Reject Match
                  </Button>
                </Box>
              </Box>
            )}
          </Paper>
        )}

        {application.processing_result?.matches && application.processing_result.matches.length > 0 && (
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Matched Identities
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Showing {application.processing_result.matches.length} potential match(es) ranked by
              similarity
            </Typography>

            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: {
                  xs: '1fr',
                  sm: 'repeat(2, 1fr)',
                  md: 'repeat(3, 1fr)',
                },
                gap: 2,
              }}
            >
              {application.processing_result.matches.map((match, index) => (
                <Card key={match.identity_id}>
                  {match.photograph_path && (
                    <CardMedia
                      component="img"
                      height="200"
                      image={match.photograph_path}
                      alt={`Match ${index + 1}`}
                      sx={{ objectFit: 'cover' }}
                    />
                  )}
                  <CardContent>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Identity ID
                    </Typography>
                    <Typography variant="body2" fontFamily="monospace" gutterBottom>
                      {match.identity_id.substring(0, 12)}...
                    </Typography>
                    <Divider sx={{ my: 1 }} />
                    <Typography variant="body2" color="text.secondary">
                      Similarity Score
                    </Typography>
                    <Typography variant="h6" color="primary">
                      {(match.similarity_score * 100).toFixed(2)}%
                    </Typography>
                  </CardContent>
                </Card>
              ))}
            </Box>
          </Paper>
        )}
      </Box>
    </DashboardLayout>
  );
};
