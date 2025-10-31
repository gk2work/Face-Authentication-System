# Security Implementation Guide

This document describes the security features implemented in the Face Authentication and De-duplication System.

## Overview

The system implements multiple layers of security to protect sensitive applicant data, facial biometrics, and system access:

1. **Authentication & Authorization** - JWT-based authentication with role-based access control
2. **Password Security** - Bcrypt hashing for password storage
3. **Rate Limiting** - Protection against brute force and DoS attacks
4. **Data Protection** - Encryption, secure file permissions, and environment variable protection
5. **CORS Configuration** - Controlled cross-origin resource sharing
6. **HTTPS/TLS** - Encrypted data transmission (production)

## Authentication System

### JWT Token-Based Authentication

The system uses JSON Web Tokens (JWT) for stateless authentication:

- **Algorithm**: HS256 (HMAC with SHA-256)
- **Token Expiration**: 30 minutes (configurable)
- **Token Contents**: Username and user roles

### Login Flow

```
1. User submits credentials (username + password)
2. System validates credentials against database
3. System generates JWT token with user info
4. Client stores token and includes in subsequent requests
5. System validates token on each protected endpoint
```

### API Endpoints

#### Login

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "your-password"
}

Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### Register User

```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "username": "newuser",
  "email": "user@example.com",
  "password": "securepassword",
  "full_name": "John Doe",
  "roles": ["reviewer"]
}
```

#### Get Current User

```http
GET /api/v1/auth/me
Authorization: Bearer <token>

Response:
{
  "username": "admin",
  "email": "admin@example.com",
  "full_name": "System Administrator",
  "roles": ["admin"],
  "is_active": true,
  "created_at": "2024-01-01T00:00:00",
  "last_login": "2024-01-15T10:30:00"
}
```

### Using Authentication in Requests

Include the JWT token in the Authorization header:

```bash
curl -H "Authorization: Bearer <your-token>" \
  https://api.example.com/api/v1/admin/duplicates
```

## Role-Based Access Control (RBAC)

### User Roles

The system defines four user roles with different permission levels:

| Role         | Description          | Permissions                                          |
| ------------ | -------------------- | ---------------------------------------------------- |
| **admin**    | System administrator | Full access to all endpoints, can override decisions |
| **reviewer** | Application reviewer | Can view and review duplicate cases                  |
| **auditor**  | Audit log viewer     | Can view audit logs and reports                      |
| **operator** | Basic operator       | Can submit applications and check status             |

### Protected Endpoints

#### Admin-Only Endpoints

- `POST /api/v1/admin/duplicates/{case_id}/override` - Override duplicate decisions

#### Admin or Reviewer Endpoints

- `GET /api/v1/admin/duplicates` - List duplicate cases
- `GET /api/v1/admin/duplicates/{case_id}` - View duplicate case details

### Implementation

Role-based access is enforced using FastAPI dependencies:

```python
from app.api.dependencies import require_admin, require_admin_or_reviewer

@router.post("/admin/duplicates/{case_id}/override")
async def override_decision(
    case_id: str,
    current_user: User = Depends(require_admin),  # Only admins
    ...
):
    # Endpoint logic
    pass
```

## Password Security

### Bcrypt Hashing

All passwords are hashed using bcrypt with automatic salt generation:

- **Algorithm**: bcrypt
- **Work Factor**: Default (automatically adjusted)
- **Salt**: Automatically generated per password

### Password Requirements

- Minimum length: 8 characters
- Recommended: Mix of uppercase, lowercase, numbers, and special characters

### Password Storage

Passwords are NEVER stored in plain text. Only bcrypt hashes are stored in the database:

```python
# Hashing
hashed = auth_service.get_password_hash("plain_password")

# Verification
is_valid = auth_service.verify_password("plain_password", hashed)
```

## Rate Limiting

Rate limiting protects against brute force attacks and API abuse using the `slowapi` library.

### Rate Limits by Endpoint

| Endpoint                     | Rate Limit         | Purpose                     |
| ---------------------------- | ------------------ | --------------------------- |
| `POST /api/v1/auth/login`    | 5 requests/minute  | Prevent brute force attacks |
| `POST /api/v1/auth/register` | 3 requests/hour    | Prevent spam registrations  |
| `POST /api/v1/applications`  | 10 requests/minute | Prevent application spam    |

### Rate Limit Response

When rate limit is exceeded:

```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json

{
  "detail": "Rate limit exceeded: 5 per 1 minute"
}
```

### Customizing Rate Limits

Rate limits can be adjusted in the endpoint decorators:

```python
@router.post("/endpoint")
@limiter.limit("10/minute")  # 10 requests per minute
async def endpoint(request: Request, ...):
    pass
```

## Data Protection

### File Permissions

Stored photographs have secure file permissions:

- **Files**: 600 (read/write for owner only)
- **Directories**: 700 (read/write/execute for owner only)

This is automatically applied when photographs are saved:

```python
# Automatic secure permissions
photograph_service.save_photograph(app_id, image, format)
# File is saved with 600 permissions
```

### Environment Variable Protection

Sensitive configuration is validated on startup:

- **Required Variables**: MONGODB_URI, SECRET_KEY
- **Validation**: Checks for missing or weak values
- **Warnings**: Logs warnings for default/weak values

### Secret Key Requirements

The SECRET_KEY must be:

- Minimum 32 characters
- Cryptographically random
- Changed from default value

Generate a strong key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Data Masking

Sensitive data is masked in logs:

```python
from app.core.security import security_manager

# Mask sensitive data
masked = security_manager.mask_sensitive_data("secret123", visible_chars=3)
# Output: "*******123"
```

## CORS Configuration

Cross-Origin Resource Sharing (CORS) is configured based on environment:

### Development

```python
allowed_origins = ["*"]  # Allow all origins
```

### Production

```python
allowed_origins = [
    "https://yourdomain.com",
    "https://admin.yourdomain.com"
]
```

### Configuration

Update `app/main.py` to add allowed origins:

```python
allowed_origins = [
    "https://yourdomain.com",
    "https://api.yourdomain.com",
]
```

## HTTPS/TLS Configuration

See [HTTPS_CONFIGURATION.md](./HTTPS_CONFIGURATION.md) for detailed HTTPS setup instructions.

### Quick Setup

For production, HTTPS is mandatory. Use one of these methods:

1. **Nginx Reverse Proxy** (Recommended)
2. **Uvicorn with SSL Certificates**
3. **Docker with Traefik**

### Minimum TLS Version

- **Required**: TLS 1.2 or higher
- **Recommended**: TLS 1.3

## Creating the First Admin User

Use the provided script to create the initial admin user from the backend directory:

```bash
cd backend
python scripts/create_admin_user.py
```

Follow the prompts to enter:

- Username
- Email
- Full name
- Password

## Security Best Practices

### For Administrators

1. **Strong Passwords**
   - Use passwords with 12+ characters
   - Mix uppercase, lowercase, numbers, and symbols
   - Use a password manager

2. **Token Management**
   - Tokens expire after 30 minutes
   - Don't share tokens
   - Store tokens securely (not in localStorage for sensitive apps)

3. **Access Control**
   - Grant minimum required permissions
   - Regularly review user access
   - Disable inactive accounts

4. **Monitoring**
   - Review audit logs regularly
   - Monitor failed login attempts
   - Set up alerts for suspicious activity

### For Developers

1. **Environment Variables**
   - Never commit `.env` files
   - Use strong SECRET_KEY in production
   - Rotate secrets regularly

2. **Dependencies**
   - Keep dependencies updated
   - Review security advisories
   - Use `pip-audit` to check for vulnerabilities

3. **Code Security**
   - Validate all user input
   - Use parameterized queries
   - Sanitize file uploads
   - Follow OWASP guidelines

4. **Logging**
   - Never log passwords or tokens
   - Mask sensitive data in logs
   - Use structured logging

## Security Checklist

### Pre-Production

- [ ] Change SECRET_KEY from default
- [ ] Configure HTTPS/TLS
- [ ] Set up specific CORS origins
- [ ] Create admin user with strong password
- [ ] Configure rate limiting
- [ ] Set secure file permissions
- [ ] Enable audit logging
- [ ] Configure MongoDB authentication
- [ ] Set up Redis password (if using)
- [ ] Review and test all endpoints

### Post-Deployment

- [ ] Monitor failed login attempts
- [ ] Review audit logs weekly
- [ ] Update dependencies monthly
- [ ] Rotate secrets quarterly
- [ ] Review user access quarterly
- [ ] Test backup and recovery
- [ ] Conduct security audit annually

## Incident Response

### Suspected Breach

1. **Immediate Actions**
   - Disable affected user accounts
   - Rotate SECRET_KEY
   - Review audit logs
   - Check for unauthorized access

2. **Investigation**
   - Identify scope of breach
   - Determine data accessed
   - Review system logs
   - Document findings

3. **Remediation**
   - Patch vulnerabilities
   - Reset affected passwords
   - Notify affected users
   - Update security measures

4. **Prevention**
   - Implement additional controls
   - Update security policies
   - Conduct security training
   - Schedule security audit

## Compliance

### Data Protection

The system implements security measures to support compliance with:

- Data encryption at rest and in transit
- Access control and authentication
- Audit logging
- Data retention policies
- Right to deletion (GDPR)

### Audit Trail

All security-relevant events are logged:

- User login/logout
- Failed authentication attempts
- Access to sensitive data
- Administrative actions
- Override decisions

## Support and Reporting

### Security Issues

To report security vulnerabilities:

1. **Do not** create public GitHub issues
2. Email security concerns to: security@yourdomain.com
3. Include detailed description and reproduction steps
4. Allow reasonable time for response

### Questions

For security-related questions:

- Review this documentation
- Check the FAQ
- Contact the security team

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [Bcrypt Documentation](https://github.com/pyca/bcrypt/)
