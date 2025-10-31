import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  Chip,
  Button,
  Alert,
  CircularProgress,
  ImageList,
  ImageListItem,
  Dialog,
  DialogContent,
  IconButton,
} from '@mui/material';
import {
  Timeline,
  TimelineItem,
  TimelineSeparator,
  TimelineConnector,
  TimelineContent,
  TimelineDot,
  TimelineOppositeContent,
} from '@mui/lab';
import {
  ArrowBack as BackIcon,
  Close as CloseIcon,
  CheckCircle as CompletedIcon,
  Error as FailedIcon,
  HourglassEmpty as PendingIcon,
  Sync as ProcessingIcon,
} from '@mui/icons-material';
import { DashboardLayout } from '@/components';
import { useIdentity } from '@/hooks/useIdentity';

const getStatusColor = (
  status: string
): 'default' | 'primary' | 'secondary' | 'error' | 'warning' | 'info' | 'success' => {
  switch (status) {
    case 'active':
      return 'success';
    case 'flagged':
      return 'warning';
    case 'merged':
      return 'info';
    default:
      return 'default';
  }
};

const getApplicationStatusIcon = (status: string) => {
  switch (status) {
    case 'completed':
      return <CompletedIcon />;
    case 'failed':
      return <FailedIcon />;
    case 'processing':
      return <ProcessingIcon />;
    case 'pending':
      return <PendingIcon />;
    default:
      return <PendingIcon />;
  }
};

const getApplicationStatusColor = (status: string): 'grey' | 'success' | 'error' | 'info' | 'warning' => {
  switch (status) {
    case 'completed':
      return 'success';
    case 'failed':
      return 'error';
    case 'processing':
      return 'info';
    case 'pending':
      return 'warning';
    default:
      return 'grey';
  }
};

export const IdentityDetailPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [selectedImage, setSelectedImage] = useState<string | null>(null);

  const { identity, applications, loading, error } = useIdentity(id);

  const handleImageClick = (imagePath: string) => {
    setSelectedImage(imagePath);
  };

  const handleCloseDialog = () => {
    setSelectedImage(null);
  };

  const handleApplicationClick = (applicationId: string) => {
    navigate(`/applications/${applicationId}`);
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

  if (error || !identity) {
    return (
      <DashboardLayout>
        <Box>
          <Button startIcon={<BackIcon />} onClick={() => navigate('/identities')} sx={{ mb: 3 }}>
            Back to Identities
          </Button>
          <Alert severity="error">{error || 'Identity not found'}</Alert>
        </Box>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <Box>
        <Button startIcon={<BackIcon />} onClick={() => navigate('/identities')} sx={{ mb: 3 }}>
          Back to Identities
        </Button>

        <Typography variant="h4" component="h1" gutterBottom>
          Identity Details
        </Typography>

        <Paper sx={{ p: 3, mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h6">Basic Information</Typography>
            <Chip
              label={identity.status}
              color={getStatusColor(identity.status)}
              sx={{ textTransform: 'capitalize' }}
            />
          </Box>

          <Box sx={{ display: 'grid', gap: 2 }}>
            <Box>
              <Typography variant="body2" color="text.secondary">
                Identity ID
              </Typography>
              <Typography variant="body1" fontFamily="monospace">
                {identity.unique_id}
              </Typography>
            </Box>

            <Box>
              <Typography variant="body2" color="text.secondary">
                Created
              </Typography>
              <Typography variant="body1">
                {new Date(identity.created_at).toLocaleString()}
              </Typography>
            </Box>

            {identity.updated_at && (
              <Box>
                <Typography variant="body2" color="text.secondary">
                  Last Updated
                </Typography>
                <Typography variant="body1">
                  {new Date(identity.updated_at).toLocaleString()}
                </Typography>
              </Box>
            )}

            <Box>
              <Typography variant="body2" color="text.secondary">
                Total Applications
              </Typography>
              <Typography variant="body1">{identity.application_count}</Typography>
            </Box>

            <Box>
              <Typography variant="body2" color="text.secondary">
                Total Photographs
              </Typography>
              <Typography variant="body1">{identity.photographs?.length || 0}</Typography>
            </Box>
          </Box>
        </Paper>

        {identity.photographs && identity.photographs.length > 0 && (
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Photograph Gallery
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Click on any image to view full size
            </Typography>
            <ImageList
              sx={{ width: '100%', maxHeight: 500 }}
              cols={4}
              rowHeight={200}
              gap={8}
            >
              {identity.photographs.map((photo, index) => (
                <ImageListItem
                  key={index}
                  sx={{
                    cursor: 'pointer',
                    '&:hover': {
                      opacity: 0.8,
                    },
                  }}
                  onClick={() => handleImageClick(photo)}
                >
                  <img
                    src={photo}
                    alt={`Photo ${index + 1}`}
                    loading="lazy"
                    style={{ objectFit: 'cover', height: '100%' }}
                  />
                </ImageListItem>
              ))}
            </ImageList>
          </Paper>
        )}

        {applications && applications.length > 0 && (
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Application History
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Timeline of all applications associated with this identity
            </Typography>

            <Timeline position="right">
              {applications.map((app, index) => (
                <TimelineItem key={app.application_id}>
                  <TimelineOppositeContent color="text.secondary" sx={{ flex: 0.3 }}>
                    <Typography variant="body2">
                      {new Date(app.created_at).toLocaleDateString()}
                    </Typography>
                    <Typography variant="caption">
                      {new Date(app.created_at).toLocaleTimeString()}
                    </Typography>
                  </TimelineOppositeContent>
                  <TimelineSeparator>
                    <TimelineDot color={getApplicationStatusColor(app.status)}>
                      {getApplicationStatusIcon(app.status)}
                    </TimelineDot>
                    {index < applications.length - 1 && <TimelineConnector />}
                  </TimelineSeparator>
                  <TimelineContent>
                    <Paper
                      elevation={2}
                      sx={{
                        p: 2,
                        cursor: 'pointer',
                        '&:hover': {
                          bgcolor: 'action.hover',
                        },
                      }}
                      onClick={() => handleApplicationClick(app.application_id)}
                    >
                      <Typography variant="body2" fontFamily="monospace" gutterBottom>
                        {app.application_id.substring(0, 16)}...
                      </Typography>
                      <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap' }}>
                        <Chip
                          label={app.status}
                          size="small"
                          sx={{ textTransform: 'capitalize' }}
                        />
                        {app.is_duplicate && (
                          <Chip label="Duplicate" color="warning" size="small" />
                        )}
                        {app.confidence_score !== undefined && (
                          <Typography variant="caption" color="text.secondary">
                            Confidence: {(app.confidence_score * 100).toFixed(1)}%
                          </Typography>
                        )}
                      </Box>
                    </Paper>
                  </TimelineContent>
                </TimelineItem>
              ))}
            </Timeline>
          </Paper>
        )}

        <Dialog
          open={!!selectedImage}
          onClose={handleCloseDialog}
          maxWidth="lg"
          fullWidth
        >
          <IconButton
            onClick={handleCloseDialog}
            sx={{
              position: 'absolute',
              right: 8,
              top: 8,
              color: 'white',
              bgcolor: 'rgba(0, 0, 0, 0.5)',
              '&:hover': {
                bgcolor: 'rgba(0, 0, 0, 0.7)',
              },
            }}
          >
            <CloseIcon />
          </IconButton>
          <DialogContent sx={{ p: 0, bgcolor: 'black' }}>
            {selectedImage && (
              <img
                src={selectedImage}
                alt="Full size"
                style={{
                  width: '100%',
                  height: 'auto',
                  display: 'block',
                }}
              />
            )}
          </DialogContent>
        </Dialog>
      </Box>
    </DashboardLayout>
  );
};
