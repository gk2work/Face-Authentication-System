import { useState } from 'react';
import type { ChangeEvent, DragEvent } from 'react';
import {
  Box,
  Typography,
  Paper,
  Button,
  Alert,
  TextField,
  LinearProgress,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Close as CloseIcon,
  CheckCircle as SuccessIcon,
} from '@mui/icons-material';
import { DashboardLayout } from '@/components';
import { api } from '@/services';

interface UploadFormData {
  metadata?: string;
}

interface ProcessingStatus {
  stage: string;
  message: string;
  progress: number;
}

export const UploadPage = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [formData, setFormData] = useState<UploadFormData>({});
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [processingStatus, setProcessingStatus] = useState<ProcessingStatus | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);

  const validateFile = (file: File): boolean => {
    // Check file type
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png'];
    if (!validTypes.includes(file.type)) {
      setValidationError('Only JPEG and PNG images are allowed');
      return false;
    }

    // Check file size (max 10MB)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
      setValidationError('File size must be less than 10MB');
      return false;
    }

    setValidationError(null);
    return true;
  };

  const handleFileSelect = (file: File) => {
    if (!validateFile(file)) {
      return;
    }

    setSelectedFile(file);
    setUploadError(null);
    setUploadSuccess(false);

    // Create preview URL
    const reader = new FileReader();
    reader.onloadend = () => {
      setPreviewUrl(reader.result as string);
    };
    reader.readAsDataURL(file);
  };

  const handleFileInputChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleDragEnter = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setIsDragging(false);

    const file = event.dataTransfer.files[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleRemoveFile = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setValidationError(null);
    setUploadError(null);
    setUploadSuccess(false);
    setProcessingStatus(null);
  };

  const handleSubmit = async () => {
    if (!selectedFile) {
      return;
    }

    setIsUploading(true);
    setUploadError(null);
    setUploadSuccess(false);
    setProcessingStatus({ stage: 'uploading', message: 'Uploading image...', progress: 0 });

    try {
      const formDataToSend = new FormData();
      formDataToSend.append('file', selectedFile);
      if (formData.metadata) {
        formDataToSend.append('metadata', formData.metadata);
      }

      // Simulate processing stages for now
      // TODO: Replace with actual WebSocket connection for real-time updates
      setProcessingStatus({ stage: 'uploading', message: 'Uploading image...', progress: 25 });
      
      await api.post('/api/v1/applications/upload', formDataToSend, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setProcessingStatus({ stage: 'detecting', message: 'Detecting face...', progress: 50 });
      await new Promise(resolve => setTimeout(resolve, 1000));

      setProcessingStatus({ stage: 'embedding', message: 'Generating face embedding...', progress: 75 });
      await new Promise(resolve => setTimeout(resolve, 1000));

      setProcessingStatus({ stage: 'comparing', message: 'Checking for duplicates...', progress: 90 });
      await new Promise(resolve => setTimeout(resolve, 1000));

      setProcessingStatus({ stage: 'complete', message: 'Processing complete!', progress: 100 });
      setUploadSuccess(true);

      // Reset form after success
      setTimeout(() => {
        handleRemoveFile();
        setFormData({});
      }, 3000);
    } catch (error: any) {
      setUploadError(
        error.response?.data?.message || 
        error.message || 
        'Failed to upload image. Please try again.'
      );
      setProcessingStatus(null);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <DashboardLayout>
      <Box>
        <Typography variant="h4" component="h1" gutterBottom>
          Upload Application
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
          Upload a photograph for face recognition and duplicate detection
        </Typography>

        {uploadError && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setUploadError(null)}>
            {uploadError}
          </Alert>
        )}

        {uploadSuccess && (
          <Alert severity="success" sx={{ mb: 3 }} icon={<SuccessIcon />}>
            Application uploaded and processed successfully!
          </Alert>
        )}

        {validationError && (
          <Alert severity="warning" sx={{ mb: 3 }} onClose={() => setValidationError(null)}>
            {validationError}
          </Alert>
        )}

        <Box sx={{ maxWidth: 800, mx: 'auto' }}>
          {!selectedFile ? (
            <Paper
              onDragEnter={handleDragEnter}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              sx={{
                p: 6,
                textAlign: 'center',
                border: '2px dashed',
                borderColor: isDragging ? 'primary.main' : 'divider',
                bgcolor: isDragging ? 'action.hover' : 'background.paper',
                cursor: 'pointer',
                transition: 'all 0.3s',
                '&:hover': {
                  borderColor: 'primary.main',
                  bgcolor: 'action.hover',
                },
              }}
              onClick={() => document.getElementById('file-input')?.click()}
            >
              <UploadIcon sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                Drag and drop an image here
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                or click to browse
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Supported formats: JPEG, PNG (max 10MB)
              </Typography>
              <input
                id="file-input"
                type="file"
                accept="image/jpeg,image/jpg,image/png"
                onChange={handleFileInputChange}
                style={{ display: 'none' }}
              />
            </Paper>
          ) : (
            <Box>
              <Paper sx={{ p: 3, mb: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6">Selected Image</Typography>
                  <Button
                    startIcon={<CloseIcon />}
                    onClick={handleRemoveFile}
                    disabled={isUploading}
                  >
                    Remove
                  </Button>
                </Box>

                {previewUrl && (
                  <Box
                    sx={{
                      width: '100%',
                      maxHeight: 400,
                      display: 'flex',
                      justifyContent: 'center',
                      mb: 2,
                    }}
                  >
                    <img
                      src={previewUrl}
                      alt="Preview"
                      style={{
                        maxWidth: '100%',
                        maxHeight: 400,
                        objectFit: 'contain',
                      }}
                    />
                  </Box>
                )}

                <Box sx={{ display: 'flex', gap: 2, color: 'text.secondary' }}>
                  <Typography variant="body2">
                    <strong>File:</strong> {selectedFile.name}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Size:</strong> {(selectedFile.size / 1024).toFixed(2)} KB
                  </Typography>
                </Box>
              </Paper>

              <Paper sx={{ p: 3, mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Additional Information (Optional)
                </Typography>
                <TextField
                  fullWidth
                  label="Metadata"
                  multiline
                  rows={3}
                  value={formData.metadata || ''}
                  onChange={(e) => setFormData({ ...formData, metadata: e.target.value })}
                  disabled={isUploading}
                  placeholder="Add any additional notes or metadata..."
                />
              </Paper>

              {processingStatus && (
                <Paper sx={{ p: 3, mb: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    Processing Status
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {processingStatus.message}
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={processingStatus.progress}
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                    {processingStatus.progress}% complete
                  </Typography>
                </Paper>
              )}

              <Button
                fullWidth
                variant="contained"
                size="large"
                startIcon={<UploadIcon />}
                onClick={handleSubmit}
                disabled={isUploading || uploadSuccess}
              >
                {isUploading ? 'Processing...' : 'Submit Application'}
              </Button>
            </Box>
          )}
        </Box>
      </Box>
    </DashboardLayout>
  );
};
