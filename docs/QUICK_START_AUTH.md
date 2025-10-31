# Quick Start: Authentication & Security

This guide will help you quickly set up and use the authentication system.

## Prerequisites

1. MongoDB connection configured in `.env`
2. Dependencies installed: `pip install -r requirements.txt`
3. Application running: `python run.py`

## Step 1: Create Admin User

Run the admin user creation script:

```bash
python scripts/create_admin_user.py
```

Follow the prompts:

```
Enter admin username: admin
Enter admin email: admin@example.com
Enter admin full name: System Administrator
Enter admin password (min 8 characters): ********
Confirm password: ********
```

## Step 2: Login and Get Token

### Using cURL

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "your-password"
  }'
```

### Response

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

Save the `access_token` for subsequent requests.

## Step 3: Use Token to Access Protected Endpoints

### Get Current User Info

```bash
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Access Admin Endpoints

```bash
# List duplicate cases (requires admin or reviewer role)
curl -X GET http://localhost:8000/api/v1/admin/duplicates \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Get specific case details
curl -X GET http://localhost:8000/api/v1/admin/duplicates/CASE_ID \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Override duplicate decision (requires admin role)
curl -X POST http://localhost:8000/api/v1/admin/duplicates/CASE_ID/override \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "decision": "reject_duplicate",
    "justification": "Manual review confirmed these are different individuals"
  }'
```

## Step 4: Create Additional Users

### Create a Reviewer User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "reviewer1",
    "email": "reviewer1@example.com",
    "password": "securepassword123",
    "full_name": "Jane Reviewer",
    "roles": ["reviewer"]
  }'
```

### Create an Auditor User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "auditor1",
    "email": "auditor1@example.com",
    "password": "securepassword123",
    "full_name": "John Auditor",
    "roles": ["auditor"]
  }'
```

## Using Python Requests

```python
import requests

# Base URL
BASE_URL = "http://localhost:8000/api/v1"

# Login
response = requests.post(
    f"{BASE_URL}/auth/login",
    json={
        "username": "admin",
        "password": "your-password"
    }
)
token = response.json()["access_token"]

# Use token in subsequent requests
headers = {"Authorization": f"Bearer {token}"}

# Get current user
user_response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
print(user_response.json())

# Access admin endpoint
duplicates_response = requests.get(
    f"{BASE_URL}/admin/duplicates",
    headers=headers
)
print(duplicates_response.json())
```

## Using JavaScript/Fetch

```javascript
const BASE_URL = "http://localhost:8000/api/v1";

// Login
async function login(username, password) {
  const response = await fetch(`${BASE_URL}/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ username, password }),
  });

  const data = await response.json();
  return data.access_token;
}

// Use token
async function getCurrentUser(token) {
  const response = await fetch(`${BASE_URL}/auth/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  return await response.json();
}

// Example usage
const token = await login("admin", "your-password");
const user = await getCurrentUser(token);
console.log(user);
```

## Common Issues

### 401 Unauthorized

**Problem**: Token is invalid or expired

**Solution**:

- Login again to get a new token
- Tokens expire after 30 minutes
- Check that you're including the "Bearer " prefix

### 403 Forbidden

**Problem**: User doesn't have required role

**Solution**:

- Check user roles: `GET /api/v1/auth/me`
- Ensure user has appropriate role for the endpoint
- Admin endpoints require admin or reviewer role

### 429 Too Many Requests

**Problem**: Rate limit exceeded

**Solution**:

- Wait before retrying
- Login: 5 requests/minute
- Register: 3 requests/hour
- Applications: 10 requests/minute

## User Roles and Permissions

| Role     | Can Login | View Duplicates | Override Decisions | View Audit Logs | Submit Applications |
| -------- | --------- | --------------- | ------------------ | --------------- | ------------------- |
| admin    | ✓         | ✓               | ✓                  | ✓               | ✓                   |
| reviewer | ✓         | ✓               | ✗                  | ✗               | ✓                   |
| auditor  | ✓         | ✗               | ✗                  | ✓               | ✓                   |
| operator | ✓         | ✗               | ✗                  | ✗               | ✓                   |

## Token Management

### Token Expiration

Tokens expire after 30 minutes. To change this, update `.env`:

```bash
ACCESS_TOKEN_EXPIRE_MINUTES=60  # 1 hour
```

### Token Storage

**Frontend Applications:**

- Store in memory (most secure)
- Use httpOnly cookies (recommended)
- Avoid localStorage for sensitive apps

**Backend/Scripts:**

- Store in environment variables
- Use secure credential management
- Rotate regularly

## Security Best Practices

1. **Strong Passwords**
   - Minimum 8 characters
   - Mix of uppercase, lowercase, numbers, symbols

2. **Token Security**
   - Never share tokens
   - Don't log tokens
   - Use HTTPS in production

3. **Role Management**
   - Grant minimum required permissions
   - Review user access regularly
   - Disable inactive accounts

4. **Production Setup**
   - Change SECRET_KEY from default
   - Enable HTTPS/TLS
   - Configure specific CORS origins
   - Set up monitoring

## Next Steps

1. **Development**: Continue building features with authentication
2. **Testing**: Test all authentication flows
3. **Production**: Follow [HTTPS_CONFIGURATION.md](./HTTPS_CONFIGURATION.md)
4. **Security**: Review [SECURITY.md](./SECURITY.md)

## Support

For detailed documentation:

- [SECURITY.md](./SECURITY.md) - Complete security guide
- [HTTPS_CONFIGURATION.md](./HTTPS_CONFIGURATION.md) - Production HTTPS setup
- [TASK_8_SUMMARY.md](./TASK_8_SUMMARY.md) - Implementation details
