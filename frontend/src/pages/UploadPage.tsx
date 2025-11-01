import { useState } from 'react';
import type { ChangeEvent, DragEvent, FormEvent } from 'react';
import {
  Box,
  Typography,
  Paper,
  Button,
  Alert,
  TextField,
  LinearProgress,
  Container,
  Grid,
  Stepper,
  Step,
  StepLabel,
  Card,
  CardContent,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Close as CloseIcon,
  CheckCircle as SuccessIcon,
  ArrowBack as BackIcon,
  ArrowForward as NextIcon,
} from '@mui/icons-material';
import { api } from '@/services';

interface ApplicantFormData {
  name: string;
  email: string;
  phone: string;
  date_of_birth: string;
  address: string;
}

interface ProcessingStatus {
  stage: string;
  message: string;
  progress: number;
}

export const UploadPage = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [formData, setFormData] = useState<ApplicantFormData>({
    name: '',
    email: '',
    phone: '',
    date_of_birth: '',
    address: '',
  });
  const [formErrors, setFormErrors] = useState<Partial<ApplicantFormData>>({});
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [applicationId, setApplicationId] = useState<string | null>(null);
  const [processingStatus, setProcessingStatus] = useState<ProcessingStatus | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);

  const steps = ['Applicant Details', 'Upload Photograph', 'Review & Submit'];

  // Validate applicant form
  const validateApplicantForm = (): boolean => {
    const errors: Partial<ApplicantFormData> = {};

    if (!formData.name.trim()) {
      errors.name = 'Name is required';
    }

    if (!formData.email.trim()) {
      errors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      errors.email = 'Invalid email format';
    }

    if (!formData.phone.trim()) {
      errors.phone = 'Phone number is required';
    } else if (!/^\+?[1-9]\d{1,14}$/.test(formData.phone.replace(/[\s-]/g, ''))) {
      errors.phone = 'Invalid phone number format';
    }

    if (!formData.date_of_birth) {
      errors.date_of_birth = 'Date of birth is required';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Validate file
  const validateFile = (file: File): boolean => {
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png'];
    if (!validTypes.includes(file.type)) {
      setValidationError('Only JPEG and PNG images are allowed');
      return false;
    }

    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
      setValidationError('File size must be less than 10MB');
      return false;
    }

    setValidationError(null);
    return true;
  };

  // Handle file selection
  const handleFileSelect = (file: File) => {
    if (!validateFile(file)) {
      return;
    }

    setSelectedFile(file);
    setUploadError(null);
    setUploadSuccess(false);

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
  };

  const handleNext = () => {
    if (activeStep === 0) {
      if (validateApplicantForm()) {
        setActiveStep((prev) => prev + 1);
      }
    } else if (activeStep === 1) {
      if (selectedFile) {
        setActiveStep((prev) => prev + 1);
      } else {
        setValidationError('Please upload a photograph');
      }
    }
  };

  const handleBack = () => {
    setActiveStep((prev) => prev - 1);
    setUploadError(null);
    setValidationError(null);
  };

  const handleSubmit = async () => {
    if (!selectedFile) {
      setValidationError('Please upload a photograph');
      return;
    }

    setIsUploading(true);
    setUploadError(null);
    setUploadSuccess(false);
    setProcessingStatus({ stage: 'uploading', message: 'Uploading application...', progress: 10 });

    try {
      const formDataToSend = new FormData();
      formDataToSend.append('photograph', selectedFile);
      formDataToSend.append('name', formData.name);
      formDataToSend.append('email', formData.email);
      formDataToSend.append('phone', formData.phone);
      formDataToSend.append('date_of_birth', formData.date_of_birth);
      if (formData.address) {
        formDataToSend.append('address', formData.address);
      }

      setProcessingStatus({ stage: 'uploading', message: 'Uploading application...', progress: 25 });

      const response = await api.post<{ application_id: string }>('/api/v1/applications/upload', formDataToSend, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setApplicationId(response.application_id);

      // Simulate processing stages (in production, use WebSocket for real-time updates)
      setProcessingStatus({ stage: 'detecting', message: 'Detecting face in photograph...', progress: 50 });
      await new Promise(resolve => setTimeout(resolve, 1500));

      setProcessingStatus({ stage: 'embedding', message: 'Generating face embedding...', progress: 75 });
      await new Promise(resolve => setTimeout(resolve, 1500));

      setProcessingStatus({ stage: 'comparing', message: 'Checking for duplicates...', progress: 90 });
      await new Promise(resolve => setTimeout(resolve, 1500));

      setProcessingStatus({ stage: 'complete', message: 'Application submitted successfully!', progress: 100 });
      setUploadSuccess(true);

      // Reset form after 3 seconds
      setTimeout(() => {
        handleReset();
      }, 5000);
    } catch (error: any) {
      setUploadError(
        error.response?.data?.detail?.message ||
        error.response?.data?.message ||
        error.message ||
        'Failed to submit application. Please try again.'
      );
      setProcessingStatus(null);
    } finally {
      setIsUploading(false);
    }
  };

  const handleReset = () => {
    setActiveStep(0);
    setSelectedFile(null);
    setPreviewUrl(null);
    setFormData({
      name: '',
      email: '',
      phone: '',
      date_of_birth: '',
      address: '',
    });
    setFormErrors({});
    setUploadError(null);
    setUploadSuccess(false);
    setApplicationId(null);
    setProcessingStatus(null);
    setValidationError(null);
  };

  const renderStepContent = () => {
    switch (activeStep) {
      case 0:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Enter Your Details
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Please provide accurate information as it will be used for verification
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  required
                  label="Full Name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  error={!!formErrors.name}
                  helperText={formErrors.name}
                  disabled={isUploading}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  required
                  type="email"
                  label="Email Address"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  error={!!formErrors.email}
                  helperText={formErrors.email}
                  disabled={isUploading}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  required
                  label="Phone Number"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  error={!!formErrors.phone}
                  helperText={formErrors.phone}
                  placeholder="+1234567890"
                  disabled={isUploading}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  required
                  type="date"
                  label="Date of Birth"
                  value={formData.date_of_birth}
                  onChange={(e) => setFormData({ ...formData, date_of_birth: e.target.value })}
                  error={!!formErrors.date_of_birth}
                  helperText={formErrors.date_of_birth}
                  InputLabelProps={{ shrink: true }}
                  disabled={isUploading}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Address (Optional)"
                  multiline
                  rows={3}
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  disabled={isUploading}
                />
              </Grid>
            </Grid>
          </Box>
        );

      case 1:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Upload Your Photograph
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Please upload a clear, recent photograph of your face
            </Typography>

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
                  Drag and drop your photo here
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
                <Paper sx={{ p: 3 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="h6">Selected Photo</Typography>
                    <Button startIcon={<CloseIcon />} onClick={handleRemoveFile} disabled={isUploading}>
                      Remove
                    </Button>
                  </Box>

                  {previewUrl && (
                    <Box sx={{ width: '100%', maxHeight: 400, display: 'flex', justifyContent: 'center', mb: 2 }}>
                      <img
                        src={previewUrl}
                        alt="Preview"
                        style={{ maxWidth: '100%', maxHeight: 400, objectFit: 'contain' }}
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
              </Box>
            )}
          </Box>
        );

      case 2:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Review Your Application
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Please review your information before submitting
            </Typography>

            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                      Applicant Details
                    </Typography>
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="body2"><strong>Name:</strong> {formData.name}</Typography>
                      <Typography variant="body2"><strong>Email:</strong> {formData.email}</Typography>
                      <Typography variant="body2"><strong>Phone:</strong> {formData.phone}</Typography>
                      <Typography variant="body2"><strong>Date of Birth:</strong> {formData.date_of_birth}</Typography>
                      {formData.address && (
                        <Typography variant="body2"><strong>Address:</strong> {formData.address}</Typography>
                      )}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                      Photograph
                    </Typography>
                    {previewUrl && (
                      <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center' }}>
                        <img
                          src={previewUrl}
                          alt="Preview"
                          style={{ maxWidth: '100%', maxHeight: 200, objectFit: 'contain' }}
                        />
                      </Box>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            </Grid>

            {processingStatus && (
              <Paper sx={{ p: 3, mt: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Processing Status
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {processingStatus.message}
                </Typography>
                <LinearProgress variant="determinate" value={processingStatus.progress} sx={{ height: 8, borderRadius: 4 }} />
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  {processingStatus.progress}% complete
                </Typography>
              </Paper>
            )}
          </Box>
        );

      default:
        return null;
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 8 }}>
      <Box sx={{ textAlign: 'center', mb: 6 }}>
        <Typography variant="h3" component="h1" gutterBottom fontWeight="bold">
          Application Submission
        </Typography>
        <Typography variant="h6" color="text.secondary">
          Submit your application for face authentication and verification
        </Typography>
      </Box>

      {uploadError && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setUploadError(null)}>
          {uploadError}
        </Alert>
      )}

      {uploadSuccess && applicationId && (
        <Alert severity="success" sx={{ mb: 3 }} icon={<SuccessIcon />}>
          Application submitted successfully! Your Application ID: <strong>{applicationId}</strong>
          <br />
          Please save this ID to check your application status later.
        </Alert>
      )}

      {validationError && (
        <Alert severity="warning" sx={{ mb: 3 }} onClose={() => setValidationError(null)}>
          {validationError}
        </Alert>
      )}

      <Paper sx={{ p: 4 }}>
        <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {renderStepContent()}

        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
          <Button
            disabled={activeStep === 0 || isUploading}
            onClick={handleBack}
            startIcon={<BackIcon />}
          >
            Back
          </Button>

          <Box sx={{ display: 'flex', gap: 2 }}>
            {activeStep < steps.length - 1 ? (
              <Button
                variant="contained"
                onClick={handleNext}
                endIcon={<NextIcon />}
                disabled={isUploading}
              >
                Next
              </Button>
            ) : (
              <Button
                variant="contained"
                onClick={handleSubmit}
                disabled={isUploading || uploadSuccess}
                startIcon={<UploadIcon />}
              >
                {isUploading ? 'Submitting...' : 'Submit Application'}
              </Button>
            )}
          </Box>
        </Box>
      </Paper>

      {uploadSuccess && (
        <Box sx={{ textAlign: 'center', mt: 4 }}>
          <Button variant="outlined" onClick={handleReset}>
            Submit Another Application
          </Button>
        </Box>
      )}
    </Container>
  );
};
