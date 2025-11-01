/**
 * AdminUserForm component
 * Form for creating and editing admin users with validation
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  TextField,
  Button,
  FormControl,
  FormLabel,
  FormGroup,
  FormControlLabel,
  FormHelperText,
  Checkbox,
  Switch,
  Grid,
  Alert,
  CircularProgress,
} from '@mui/material';
import { Save, Cancel } from '@mui/icons-material';
import { superadminApi } from '../services/api';
import type { AdminUser, CreateAdminUserRequest, UpdateAdminUserRequest } from '../types';

interface AdminUserFormProps {
  mode: 'create' | 'edit';
  username?: string;
  initialData?: Partial<AdminUser>;
  onSuccess?: (user: AdminUser) => void;
  onCancel?: () => void;
}

interface FormData {
  username: string;
  email: string;
  password: string;
  full_name: string;
  roles: string[];
  is_active: boolean;
}

interface FormErrors {
  username?: string;
  email?: string;
  password?: string;
  full_name?: string;
  roles?: string;
}

const AVAILABLE_ROLES = [
  { value: 'superadmin', label: 'Superadmin' },
  { value: 'admin', label: 'Admin' },
  { value: 'reviewer', label: 'Reviewer' },
  { value: 'auditor', label: 'Auditor' },
  { value: 'operator', label: 'Operator' },
];

export const AdminUserForm: React.FC<AdminUserFormProps> = ({
  mode,
  username,
  initialData,
  onSuccess,
  onCancel,
}) => {
  const [formData, setFormData] = useState<FormData>({
    username: initialData?.username || '',
    email: initialData?.email || '',
    password: '',
    full_name: initialData?.full_name || '',
    roles: initialData?.roles || [],
    is_active: initialData?.is_active ?? true,
  });

  const [errors, setErrors] = useState<FormErrors>({});
  const [loading, setLoading] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitSuccess, setSubmitSuccess] = useState(false);

  // Load user data in edit mode
  useEffect(() => {
    if (mode === 'edit' && username && !initialData) {
      const fetchUser = async () => {
        try {
          const user = await superadminApi.getAdminUser(username);
          setFormData({
            username: user.username,
            email: user.email,
            password: '',
            full_name: user.full_name,
            roles: user.roles,
            is_active: user.is_active,
          });
        } catch (err) {
          setSubmitError('Failed to load user data');
        }
      };
      fetchUser();
    }
  }, [mode, username, initialData]);

  const validateField = (name: keyof FormData, value: any): string | undefined => {
    switch (name) {
      case 'username':
        if (!value || value.length < 3) {
          return 'Username must be at least 3 characters';
        }
        if (value.length > 50) {
          return 'Username must not exceed 50 characters';
        }
        if (!/^[a-zA-Z0-9_-]+$/.test(value)) {
          return 'Username can only contain letters, numbers, hyphens, and underscores';
        }
        break;

      case 'email':
        if (!value) {
          return 'Email is required';
        }
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
          return 'Invalid email format';
        }
        break;

      case 'password':
        if (mode === 'create' && !value) {
          return 'Password is required';
        }
        if (value && value.length < 8) {
          return 'Password must be at least 8 characters';
        }
        break;

      case 'full_name':
        if (!value || value.length < 1) {
          return 'Full name is required';
        }
        if (value.length > 200) {
          return 'Full name must not exceed 200 characters';
        }
        break;

      case 'roles':
        if (!value || value.length === 0) {
          return 'At least one role must be selected';
        }
        break;
    }
    return undefined;
  };

  const handleChange = (field: keyof FormData) => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const value = event.target.value;
    setFormData((prev) => ({ ...prev, [field]: value }));
    
    // Clear error when user starts typing
    if (errors[field as keyof FormErrors]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  };

  const handleRoleChange = (role: string) => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const checked = event.target.checked;
    setFormData((prev) => ({
      ...prev,
      roles: checked
        ? [...prev.roles, role]
        : prev.roles.filter((r) => r !== role),
    }));
    
    // Clear role error
    if (errors.roles) {
      setErrors((prev) => ({ ...prev, roles: undefined }));
    }
  };

  const handleActiveChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({ ...prev, is_active: event.target.checked }));
  };

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    newErrors.username = validateField('username', formData.username);
    newErrors.email = validateField('email', formData.email);
    newErrors.password = validateField('password', formData.password);
    newErrors.full_name = validateField('full_name', formData.full_name);
    newErrors.roles = validateField('roles', formData.roles);

    setErrors(newErrors);

    return !Object.values(newErrors).some((error) => error !== undefined);
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setSubmitError(null);
    setSubmitSuccess(false);

    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      if (mode === 'create') {
        const createData: CreateAdminUserRequest = {
          username: formData.username,
          email: formData.email,
          password: formData.password,
          full_name: formData.full_name,
          roles: formData.roles,
        };
        const user = await superadminApi.createAdminUser(createData);
        setSubmitSuccess(true);
        if (onSuccess) {
          onSuccess(user);
        }
      } else {
        const updateData: UpdateAdminUserRequest = {
          email: formData.email,
          full_name: formData.full_name,
          roles: formData.roles,
          is_active: formData.is_active,
        };
        const user = await superadminApi.updateAdminUser(formData.username, updateData);
        setSubmitSuccess(true);
        if (onSuccess) {
          onSuccess(user);
        }
      }
    } catch (err: any) {
      setSubmitError(
        err.response?.data?.detail || err.message || 'Failed to save user'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box component="form" onSubmit={handleSubmit} noValidate>
      {submitError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {submitError}
        </Alert>
      )}

      {submitSuccess && (
        <Alert severity="success" sx={{ mb: 2 }}>
          User {mode === 'create' ? 'created' : 'updated'} successfully!
        </Alert>
      )}

      <Grid container spacing={2}>
        {/* Username */}
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            required
            label="Username"
            name="username"
            value={formData.username}
            onChange={handleChange('username')}
            error={!!errors.username}
            helperText={errors.username}
            disabled={mode === 'edit'}
            inputProps={{
              'aria-label': 'Username',
              minLength: 3,
              maxLength: 50,
            }}
          />
        </Grid>

        {/* Email */}
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            required
            type="email"
            label="Email"
            name="email"
            value={formData.email}
            onChange={handleChange('email')}
            error={!!errors.email}
            helperText={errors.email}
            inputProps={{
              'aria-label': 'Email address',
            }}
          />
        </Grid>

        {/* Password (only in create mode) */}
        {mode === 'create' && (
          <Grid item xs={12}>
            <TextField
              fullWidth
              required
              type="password"
              label="Password"
              name="password"
              value={formData.password}
              onChange={handleChange('password')}
              error={!!errors.password}
              helperText={errors.password || 'Minimum 8 characters'}
              inputProps={{
                'aria-label': 'Password',
                minLength: 8,
              }}
            />
          </Grid>
        )}

        {/* Full Name */}
        <Grid item xs={12}>
          <TextField
            fullWidth
            required
            label="Full Name"
            name="full_name"
            value={formData.full_name}
            onChange={handleChange('full_name')}
            error={!!errors.full_name}
            helperText={errors.full_name}
            inputProps={{
              'aria-label': 'Full name',
              minLength: 1,
              maxLength: 200,
            }}
          />
        </Grid>

        {/* Roles */}
        <Grid item xs={12}>
          <FormControl
            required
            error={!!errors.roles}
            component="fieldset"
            variant="standard"
          >
            <FormLabel component="legend">Roles</FormLabel>
            <FormGroup>
              <Grid container>
                {AVAILABLE_ROLES.map((role) => (
                  <Grid item xs={12} sm={6} md={4} key={role.value}>
                    <FormControlLabel
                      control={
                        <Checkbox
                          checked={formData.roles.includes(role.value)}
                          onChange={handleRoleChange(role.value)}
                          name={role.value}
                          inputProps={{
                            'aria-label': `${role.label} role`,
                          }}
                        />
                      }
                      label={role.label}
                    />
                  </Grid>
                ))}
              </Grid>
            </FormGroup>
            {errors.roles && <FormHelperText>{errors.roles}</FormHelperText>}
          </FormControl>
        </Grid>

        {/* Active Status (only in edit mode) */}
        {mode === 'edit' && (
          <Grid item xs={12}>
            <FormControlLabel
              control={
                <Switch
                  checked={formData.is_active}
                  onChange={handleActiveChange}
                  name="is_active"
                  inputProps={{
                    'aria-label': 'Active status',
                  }}
                />
              }
              label="Active"
            />
          </Grid>
        )}

        {/* Action Buttons */}
        <Grid item xs={12}>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end', mt: 2 }}>
            {onCancel && (
              <Button
                variant="outlined"
                startIcon={<Cancel />}
                onClick={onCancel}
                disabled={loading}
              >
                Cancel
              </Button>
            )}
            <Button
              type="submit"
              variant="contained"
              startIcon={loading ? <CircularProgress size={20} /> : <Save />}
              disabled={loading}
            >
              {loading ? 'Saving...' : mode === 'create' ? 'Create User' : 'Save Changes'}
            </Button>
          </Box>
        </Grid>
      </Grid>
    </Box>
  );
};
