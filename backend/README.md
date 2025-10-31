# Face Authentication Backend API

This directory contains the backend API service for the Face Authentication and De-duplication System.

## 📁 Directory Structure

```
backend/
├── app/                    # FastAPI application
│   ├── api/v1/            # API endpoints
│   ├── core/              # Configuration, logging, security
│   ├── database/          # MongoDB connections and repositories
│   ├── models/            # Pydantic models
│   ├── services/          # Business logic services
│   └── utils/             # Utility functions
├── tests/                 # Test suite
├── storage/               # Data storage
│   ├── photographs/       # Applicant photographs
│   └── vector_db/         # FAISS vector index
├── logs/                  # Application logs
├── docs/                  # Backend documentation
├── config/                # Configuration files
├── scripts/               # Utility scripts
├── Dockerfile             # Container definition
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (not in git)
└── .env.example           # Environment template
```

## 🚀 Quick Start

### Using Docker (Recommended)

From the **project root** directory:

```bash
# Initialize and start all services
make init

# Or manually
docker-compose up -d
```

The API will be available at http://localhost:8000

### Local Development (Without Docker)

1. **Create virtual environment**:

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**:

```bash
pip install -r requirements.txt
```

3. **Set up environment**:

```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Create storage directories**:

```bash
mkdir -p storage/photographs storage/vector_db logs
```

5. **Start MongoDB** (if not using Docker):

```bash
docker run -d -p 27017:27017 --name mongodb mongo:6
```

6. **Run the application**:

```bash
# Development mode with hot reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
./scripts/start_production.sh
```

## 🔧 Development

### Running Tests

```bash
# From backend directory
pytest tests/ -v

# With coverage
pytest tests/ --cov=app --cov-report=html

# Specific test file
pytest tests/test_face_recognition_service.py -v
```

### Code Quality

```bash
# Format code
black app/ tests/

# Lint
flake8 app/ tests/

# Type checking
mypy app/
```

## 📚 API Documentation

Once the server is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

#### Health Checks

- `GET /health` - Basic health check
- `GET /live` - Liveness probe
- `GET /ready` - Readiness probe (checks all dependencies)

#### Applications

- `POST /api/v1/applications` - Submit single application
- `POST /api/v1/applications/batch` - Submit batch applications
- `GET /api/v1/applications/{id}/status` - Check application status
- `POST /api/v1/applications/status/batch` - Batch status query

#### Authentication

- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - User registration

#### Admin

- `GET /api/v1/admin/duplicates/pending` - Get pending reviews
- `POST /api/v1/admin/duplicates/{id}/override` - Submit review decision

#### Monitoring

- `GET /api/v1/monitoring/metrics` - System metrics
- `GET /api/v1/monitoring/performance` - Performance metrics

## ⚙️ Configuration

### Environment Variables

Key configuration options (see `.env.example` for complete list):

```bash
# Application
ENVIRONMENT=development
API_HOST=0.0.0.0
API_PORT=8000

# Database
MONGODB_URI=mongodb://localhost:27017/face_auth
MONGODB_DATABASE=face_auth

# Storage
STORAGE_PATH=./storage
VECTOR_DB_PATH=./storage/vector_db

# Security
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Face Recognition
EMBEDDING_DIMENSION=512
MIN_FACE_SIZE=80
BLUR_THRESHOLD=100.0
QUALITY_SCORE_THRESHOLD=0.5
VERIFICATION_THRESHOLD=0.85
```

### Storage Paths

All storage paths are relative to the `backend/` directory:

- **Photographs**: `./storage/photographs/`
- **Vector DB**: `./storage/vector_db/`
- **Logs**: `./logs/`

## 🐳 Docker

### Building the Image

From the **project root**:

```bash
docker-compose build
```

Or build directly:

```bash
cd backend
docker build -t face-auth-api .
```

### Running the Container

```bash
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/storage:/app/storage \
  -v $(pwd)/logs:/app/logs \
  --name face-auth-api \
  face-auth-api
```

### Container Shell Access

```bash
# Using docker-compose (from project root)
make shell

# Or directly
docker exec -it face-auth-api /bin/bash
```

## 📊 Logging

Logs are written to the `logs/` directory:

- `app_YYYY-MM-DD.log` - Human-readable logs
- `app_YYYY-MM-DD.json` - Structured JSON logs for parsing

### Log Levels

- `DEBUG` - Detailed diagnostic information
- `INFO` - General informational messages
- `WARNING` - Warning messages
- `ERROR` - Error messages
- `CRITICAL` - Critical errors

Configure log level via `LOG_LEVEL` environment variable.

## 🧪 Testing

### Test Structure

```
tests/
├── test_audit_api.py              # Audit API tests
├── test_audit_service.py          # Audit service tests
├── test_face_recognition_service.py  # Face recognition tests
├── test_identity_service.py       # Identity management tests
└── test_deduplication_service.py  # Deduplication tests
```

### Running Specific Tests

```bash
# Test face recognition
pytest tests/test_face_recognition_service.py -v

# Test with markers
pytest -m "not slow" tests/

# Test with coverage
pytest tests/ --cov=app --cov-report=term-missing
```

## 🔒 Security

### Authentication

The API uses JWT-based authentication:

1. Login via `/api/v1/auth/login` to get a token
2. Include token in requests: `Authorization: Bearer <token>`
3. Tokens expire after `ACCESS_TOKEN_EXPIRE_MINUTES` (default: 30)

### Role-Based Access Control

- **Admin**: Full access to all endpoints
- **Reviewer**: Access to review workflows
- **User**: Basic application submission

### Security Best Practices

- Never commit `.env` file
- Use strong `JWT_SECRET_KEY` in production
- Enable HTTPS in production
- Regularly update dependencies
- Review audit logs

## 🚀 Performance

### Optimization Features

- **Batch Processing**: Process multiple applications simultaneously
- **FAISS IVF Index**: Fast vector similarity search
- **Connection Pooling**: Efficient database connections
- **In-Memory Caching**: Reduce database queries

### Performance Tuning

```bash
# Adjust workers in production
uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8000

# Enable FAISS IVF optimization
FAISS_USE_IVF=true
FAISS_NLIST=100
FAISS_NPROBE=10
```

## 🐛 Troubleshooting

### Common Issues

**Import Errors**

```bash
# Ensure you're in the backend directory
cd backend

# Activate virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

**MongoDB Connection Failed**

```bash
# Check MongoDB is running
docker ps | grep mongodb

# Test connection
mongosh mongodb://localhost:27017/face_auth
```

**Storage Permission Issues**

```bash
# Fix permissions
chmod -R 755 storage/
mkdir -p storage/photographs storage/vector_db
```

**Port Already in Use**

```bash
# Find process using port 8000
lsof -i :8000

# Kill process or change port in .env
API_PORT=8001
```

## 📖 Additional Documentation

- **API Documentation**: http://localhost:8000/docs
- **Security Guide**: `docs/SECURITY.md`
- **HTTPS Configuration**: `docs/HTTPS_CONFIGURATION.md`
- **Deployment Guide**: `docs/deployment/`

## 🔗 Related

- **Project Root**: `../README.md` - Full project documentation
- **Frontend**: `../frontend/` - Frontend application (coming soon)

## 📧 Support

For backend-specific issues:

1. Check the logs in `logs/` directory
2. Review API documentation at `/docs`
3. Check environment configuration in `.env`
4. Consult troubleshooting section above

For general project support, see the main README in the project root.
