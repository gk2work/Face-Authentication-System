# Swagger API Documentation

## Overview

The Face Authentication and De-duplication System API comes with built-in interactive API documentation powered by FastAPI's automatic OpenAPI (Swagger) generation.

## Accessing the Documentation

### Swagger UI (Interactive)

- **URL**: `http://localhost:8000/docs`
- **Features**:
  - Interactive API testing
  - Try out endpoints directly from the browser
  - View request/response schemas
  - See authentication requirements

### ReDoc (Alternative View)

- **URL**: `http://localhost:8000/redoc`
- **Features**:
  - Clean, readable documentation
  - Better for reading and understanding
  - Organized by tags
  - Detailed schema documentation

### OpenAPI JSON

- **URL**: `http://localhost:8000/openapi.json`
- **Features**:
  - Raw OpenAPI 3.0 specification
  - Can be imported into Postman, Insomnia, etc.
  - Machine-readable format

## API Structure

### Base URL

```
http://localhost:8000/api/v1
```

### Authentication

All protected endpoints require JWT Bearer token authentication:

```http
Authorization: Bearer <your_jwt_token>
```

To get a token:

1. Use the `/api/v1/auth/login` endpoint
2. Provide username and password
3. Receive access token in response
4. Click "Authorize" button in Swagger UI
5. Enter: `Bearer <token>`

## API Endpoints by Category

### 🔐 Authentication (`/api/v1/auth`)

- `POST /login` - Login and get JWT token
- `POST /refresh` - Refresh access token
- `POST /logout` - Logout (invalidate token)

### 👤 Users (`/api/v1/users`)

- `GET /users` - List all users (admin only)
- `GET /users/{username}` - Get user details (admin only)
- `POST /users` - Create new user (admin only)
- `PUT /users/{username}` - Update user (admin only)
- `DELETE /users/{username}` - Deactivate user (admin only)

### 🔑 Superadmin (`/api/v1/superadmin`)

- `GET /superadmin/users` - List all users including superadmins
- `POST /superadmin/users` - Create superadmin user
- `PUT /superadmin/users/{username}/roles` - Update user roles

### 📝 Applications (`/api/v1/applications`)

- `POST /applications` - Submit new application
- `GET /applications/{application_id}` - Get application status
- `GET /applications` - List applications

### 🎭 Face Recognition (`/api/v1/face-recognition`)

- `POST /face-recognition/detect` - Detect faces in image
- `POST /face-recognition/extract` - Extract face embeddings
- `POST /face-recognition/compare` - Compare two faces

### 🔍 Admin (`/api/v1/admin`)

- `GET /admin/duplicates` - List duplicate cases
- `GET /admin/duplicates/{case_id}` - Get duplicate case details
- `POST /admin/duplicates/{case_id}/override` - Override duplicate decision
- `GET /admin/audit-logs` - Get audit logs
- `POST /admin/audit-logs/export` - Export audit logs

### 🆔 Identities (`/api/v1/identities`)

- `GET /identities/{identity_id}` - Get identity details
- `GET /identities` - List identities

### 📊 Dashboard (`/api/v1/dashboard`)

- `GET /dashboard/stats` - Get dashboard statistics
- `GET /dashboard/recent-activity` - Get recent activity

### 📈 Monitoring (`/api/v1/monitoring`)

- `GET /monitoring/metrics` - Get system metrics
- `POST /monitoring/metrics/reset` - Reset metrics
- `POST /monitoring/alerts/check` - Check alerts

### ⚙️ System (`/api/v1/system`)

- `GET /system/resilience` - Get resilience status
- `GET /system/circuit-breakers` - Get circuit breaker status
- `POST /system/circuit-breakers/reset` - Reset circuit breakers
- `GET /system/dead-letter-queue` - Get DLQ status
- `DELETE /system/dead-letter-queue` - Clear DLQ

### 🏥 Health Checks

- `GET /health` - Basic health check
- `GET /live` - Liveness probe (Kubernetes)
- `GET /ready` - Readiness probe (Kubernetes)

## Role-Based Access Control

The API implements a hierarchical role system:

### Role Hierarchy

```
superadmin (Level 5) - Full system access
    ↓
admin (Level 4) - Administrative access
    ↓
reviewer/auditor (Level 3) - Review and audit access
    ↓
operator (Level 2) - Standard operations
```

### Role Inheritance

- **Superadmin**: Can access all endpoints (admin, reviewer, auditor, operator)
- **Admin**: Can access reviewer, auditor, and operator endpoints
- **Reviewer**: Can access operator endpoints
- **Auditor**: Can access operator endpoints
- **Operator**: Base level access only

### Endpoint Access Examples

| Endpoint              | Superadmin | Admin | Reviewer | Auditor | Operator |
| --------------------- | ---------- | ----- | -------- | ------- | -------- |
| `/users`              | ✅         | ✅    | ❌       | ❌      | ❌       |
| `/admin/audit-logs`   | ✅         | ✅    | ✅       | ❌      | ❌       |
| `/monitoring/metrics` | ✅         | ✅    | ✅       | ❌      | ❌       |
| `/applications`       | ✅         | ✅    | ✅       | ✅      | ✅       |

## Using Swagger UI

### Step-by-Step Guide

1. **Start the Backend Server**

   ```bash
   cd backend
   python run.py
   ```

2. **Open Swagger UI**
   - Navigate to `http://localhost:8000/docs`

3. **Authenticate**
   - Click the "Authorize" button (🔒 icon) at the top right
   - Login first using `/api/v1/auth/login` endpoint:
     - Click "Try it out"
     - Enter credentials in request body
     - Click "Execute"
     - Copy the `access_token` from response
   - Click "Authorize" button again
   - Enter: `Bearer <your_access_token>`
   - Click "Authorize" then "Close"

4. **Test Endpoints**
   - Expand any endpoint
   - Click "Try it out"
   - Fill in parameters
   - Click "Execute"
   - View response

### Example: Testing User List Endpoint

1. Authenticate as admin or superadmin
2. Navigate to `GET /api/v1/users`
3. Click "Try it out"
4. Set parameters:
   - `skip`: 0
   - `limit`: 10
   - `is_active`: true (optional)
5. Click "Execute"
6. View the response with user list

## Request/Response Examples

### Login Request

```json
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "your_password"
}
```

### Login Response

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Create User Request

```json
POST /api/v1/users
Authorization: Bearer <token>
Content-Type: application/json

{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "SecurePassword123!",
  "full_name": "New User",
  "roles": ["operator"]
}
```

### List Users Response

```json
[
  {
    "username": "admin",
    "email": "admin@example.com",
    "full_name": "Admin User",
    "roles": ["admin"],
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

## Rate Limiting

Most endpoints are rate-limited to prevent abuse:

- Default: 100 requests per minute per IP
- Authentication endpoints: 5 requests per minute
- Exceeded limits return `429 Too Many Requests`

## Error Responses

### Standard Error Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common HTTP Status Codes

- `200 OK` - Success
- `201 Created` - Resource created
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

## Exporting Documentation

### Export to Postman

1. Download OpenAPI spec: `http://localhost:8000/openapi.json`
2. Open Postman
3. Click "Import"
4. Select the downloaded JSON file
5. All endpoints will be imported as a collection

### Export to Insomnia

1. Download OpenAPI spec: `http://localhost:8000/openapi.json`
2. Open Insomnia
3. Click "Create" → "Import"
4. Select the downloaded JSON file

## Customizing Documentation

The API documentation is automatically generated from:

- Endpoint docstrings
- Pydantic model definitions
- Type hints
- Query/Path/Body parameter descriptions

To enhance documentation for an endpoint:

```python
@router.get("/example")
async def example_endpoint(
    param1: str = Query(..., description="Description of param1"),
    param2: int = Query(10, ge=1, le=100, description="Description of param2")
):
    """
    Detailed endpoint description

    This endpoint does something important.

    - **param1**: Detailed explanation
    - **param2**: Another detailed explanation

    Returns:
        Description of return value
    """
    pass
```

## WebSocket Documentation

The API includes WebSocket endpoints for real-time updates:

### WebSocket Endpoint

```
ws://localhost:8000/api/v1/ws/{client_id}
```

**Note**: WebSocket endpoints are not fully documented in Swagger UI but are available for use.

## Additional Resources

- **API Source Code**: `backend/app/api/v1/`
- **Models**: `backend/app/models/`
- **Main App**: `backend/app/main.py`
- **Configuration**: `backend/app/core/config.py`

## Support

For issues or questions about the API:

- Check the logs in `backend/logs/`
- Review error responses for details
- Contact: support@faceauth.example.com

---

**Last Updated**: 2024
**API Version**: 1.0.0
