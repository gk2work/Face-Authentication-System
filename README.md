# Face Authentication and De-duplication System

AI-powered face authentication system for large-scale public examinations in India. This system prevents duplicate registrations and verifies applicant identities through advanced facial recognition technology.

## 🚀 Features

### Core Features

- **Automated De-duplication**: Detect duplicate applications using facial recognition with 85%+ accuracy
- **Unique Identity Management**: Assign single unique IDs to verified applicants
- **High Performance**: Process 10,000+ applications per hour with batch processing
- **Secure**: AES-256 encryption, JWT authentication, role-based access control
- **Scalable**: Horizontal scaling support with load balancing and caching
- **Comprehensive Audit Trail**: Track all operations with detailed logging
- **Webhook Notifications**: Real-time status updates via webhooks
- **Admin Review Interface**: Manual review for borderline duplicate cases

### Frontend Features

- **Interactive Dashboard**: Real-time statistics and application timeline charts
- **Application Upload**: Drag-and-drop interface with real-time processing updates via WebSocket
- **Application Management**: Search, filter, and view detailed application information
- **Identity Management**: Browse identities, view photo galleries, and application history
- **Match Visualization**: Side-by-side comparison of duplicate matches with similarity scores
- **Admin Panel**: User management, system health monitoring, and audit log viewer
- **Error Handling**: Global error boundary, retry logic, and offline detection
- **Responsive Design**: Mobile-friendly interface with Material-UI components
- **Real-time Updates**: WebSocket integration for live processing status

## 📋 Technology Stack

### Backend

- **Framework**: FastAPI (Python 3.10+)
- **Database**: MongoDB 6.0
- **Vector Search**: FAISS with IVF optimization
- **Cache**: In-memory cache with TTL
- **Face Recognition**: FaceNet (InceptionResnetV1)
- **Logging**: Loguru with structured JSON logs

### Frontend

- **Framework**: React 19 with TypeScript
- **Build Tool**: Vite 7
- **UI Library**: Material-UI (MUI) v7
- **Routing**: React Router v7
- **HTTP Client**: Axios
- **Charts**: Recharts
- **State Management**: React Hooks

### Deployment

- **Containerization**: Docker & Docker Compose
- **Web Server**: FastAPI serves both API and frontend in production

## 🗂️ Monorepo Architecture

This project uses a monorepo structure to organize code and enable scalable development:

### Why Monorepo?

- **Clear Separation**: Backend and frontend code are isolated in separate directories
- **Unified Deployment**: Single docker-compose.yml orchestrates all services
- **Shared Configuration**: Common settings and documentation at root level
- **Independent Development**: Teams can work on services independently
- **Simplified CI/CD**: Single repository for all deployment pipelines
- **Code Reuse**: Easy to share types, utilities, and documentation

### Directory Organization

- **`backend/`**: Complete backend API service with its own dependencies, tests, and documentation
- **`docker-compose.yml`**: Root-level orchestration for all services (backend, database, cache)
- **`Makefile`**: Convenient commands to manage the entire system from project root
- **`README.md`**: Project overview and getting started guide (this file)

### Development Workflows

**Backend-Only Development**: Navigate to `backend/` directory and follow instructions in `backend/README.md`

**Full-Stack Development**: Use docker-compose from root to run all services together

**Production Deployment**: Deploy entire stack using root-level docker-compose.yml

## 🏗️ Project Structure

This project uses a **monorepo structure** to organize backend and frontend code in separate directories, enabling independent development while maintaining a unified deployment strategy.

```
.
├── backend/              # Backend API service
│   ├── app/             # FastAPI application
│   │   ├── api/v1/      # API endpoints (applications, auth, admin, monitoring)
│   │   ├── core/        # Configuration, logging, security
│   │   ├── database/    # MongoDB connections and repositories
│   │   ├── models/      # Pydantic models (Application, Identity, Audit)
│   │   ├── services/    # Business logic services
│   │   │   ├── application_processor.py    # End-to-end workflow orchestrator
│   │   │   ├── face_recognition_service.py # Face detection and embedding
│   │   │   ├── deduplication_service.py    # Duplicate detection
│   │   │   ├── identity_service.py         # Identity management
│   │   │   ├── notification_service.py     # Webhook notifications
│   │   │   └── review_workflow_service.py  # Admin review workflow
│   │   └── utils/       # Utility functions and error handling
│   ├── tests/           # Backend test suite
│   ├── storage/         # Data storage
│   │   ├── photographs/ # Applicant photographs
│   │   └── vector_db/   # FAISS vector index
│   ├── logs/            # Application logs
│   ├── docs/            # Backend documentation
│   ├── config/          # Configuration files (nginx, haproxy, env)
│   ├── scripts/         # Utility scripts
│   ├── Dockerfile       # Backend container definition
│   ├── requirements.txt # Python dependencies
│   └── README.md        # Backend-specific documentation
├── frontend/            # Frontend React application
│   ├── src/            # Source code
│   │   ├── components/ # Reusable React components
│   │   ├── pages/      # Page components
│   │   ├── services/   # API client and services
│   │   ├── hooks/      # Custom React hooks
│   │   ├── types/      # TypeScript type definitions
│   │   ├── utils/      # Utility functions
│   │   ├── test/       # Test utilities and setup
│   │   └── App.tsx     # Main application component
│   ├── dist/           # Production build output
│   ├── package.json    # Node dependencies
│   ├── vite.config.ts  # Vite configuration
│   ├── vitest.config.ts # Test configuration
│   └── tsconfig.json   # TypeScript configuration
├── docker-compose.yml   # Docker orchestration for all services
├── Makefile             # Convenient commands (run from root)
└── README.md            # This file - project overview
```

### Monorepo Structure Benefits

- **Separation of Concerns**: Backend and frontend code are clearly separated
- **Independent Development**: Teams can work on backend/frontend independently
- **Unified Deployment**: Single docker-compose.yml orchestrates all services
- **Shared Resources**: Common configuration and documentation at root level
- **Future-Ready**: Easy to add frontend, mobile apps, or other services

## 🐳 Quick Start with Docker (Recommended)

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum
- 10GB disk space

### 1. Clone and Initialize

```bash
git clone <repository-url>
cd face-authentication-deduplication

# Initialize system (creates directories, builds images, starts services)
# Run from project root
make init
```

**Note**: All `make` commands should be run from the **project root** directory. The backend service is automatically configured through docker-compose.

### 2. Access the System

- **API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **MongoDB Express** (optional): http://localhost:8081 (admin/admin)

### 3. Verify Installation

```bash
# Check service health
make health

# View logs
make logs

# View API logs only
make logs-app
```

### Common Docker Commands

```bash
# Start services
make up

# Start with hot reload (development)
make up-dev

# Stop services
make down

# Restart services
make restart

# View running containers
make ps

# Open shell in app container
make shell

# Run tests
make test

# Clean everything (removes containers, volumes, images)
make clean
```

## 💻 Local Development Setup (Without Docker)

### Backend-Only Development

For detailed backend setup instructions, see [`backend/README.md`](backend/README.md).

### Prerequisites

- Python 3.10+
- MongoDB 6.0+ (local or Atlas)
- 4GB RAM minimum

### Quick Setup

1. **Navigate to backend directory**:

```bash
cd backend
```

2. **Create virtual environment**:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:

```bash
pip install -r requirements.txt
```

4. **Set up environment variables**:

```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Create storage directories**:

```bash
mkdir -p storage/photographs storage/vector_db logs
```

6. **Start MongoDB** (if running locally):

```bash
# Using Docker
docker run -d -p 27017:27017 --name mongodb mongo:6

# Or install MongoDB locally
# https://www.mongodb.com/docs/manual/installation/
```

### Running the Application

```bash
# From backend directory
cd backend

# Development mode with hot reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode with multiple workers
./scripts/start_production.sh

# Or with gunicorn
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Running Tests

```bash
# From backend directory
cd backend

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_face_recognition_service.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

### Frontend Setup

#### Prerequisites

- Node.js 18+ and npm 9+
- Backend API running (see above)

#### Installation

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env.development
# Edit .env.development if needed (default points to localhost:8000)
```

#### Development Mode

```bash
# From frontend directory
npm run dev

# Access at http://localhost:5173
```

The frontend dev server proxies API requests to the backend at `http://localhost:8000`.

#### Building for Production

```bash
# From frontend directory
npm run build

# Output will be in frontend/dist/
# Backend automatically serves this in production mode
```

#### Running Tests

```bash
# From frontend directory

# Run tests in watch mode
npm test

# Run tests once
npm run test:run

# Run with coverage
npm run test:coverage
```

### Full-Stack Development

Run both backend and frontend services:

```bash
# Terminal 1 - Backend (from backend/)
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend (from frontend/)
cd frontend
npm run dev
```

Access:

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Production Mode

In production, the backend serves the built frontend:

```bash
# Build frontend
cd frontend
npm run build

# Start backend (serves frontend automatically)
cd ../backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Access everything at: http://localhost:8000

## 📚 API Documentation

### Health Checks

```bash
# Basic health check
curl http://localhost:8000/health

# Liveness probe (Kubernetes)
curl http://localhost:8000/live

# Readiness probe (comprehensive)
curl http://localhost:8000/ready
```

### Application Submission

```bash
# Submit single application
curl -X POST http://localhost:8000/api/v1/applications \
  -H "Content-Type: application/json" \
  -d '{
    "applicant_data": {
      "name": "John Doe",
      "email": "john@example.com",
      "phone": "1234567890",
      "date_of_birth": "1990-01-01"
    },
    "photograph_base64": "<base64-encoded-image>",
    "photograph_format": "jpg"
  }'

# Check application status
curl http://localhost:8000/api/v1/applications/{application_id}/status

# Batch submission (up to 100 applications)
curl -X POST http://localhost:8000/api/v1/applications/batch \
  -H "Content-Type: application/json" \
  -d '[{...}, {...}]'

# Batch status query
curl -X POST http://localhost:8000/api/v1/applications/status/batch \
  -H "Content-Type: application/json" \
  -d '["app-id-1", "app-id-2", "app-id-3"]'
```

### Authentication

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"

# Use token in requests
curl http://localhost:8000/api/v1/admin/duplicates \
  -H "Authorization: Bearer <your-token>"
```

### Admin Endpoints

```bash
# Get pending reviews
curl http://localhost:8000/api/v1/admin/duplicates/pending \
  -H "Authorization: Bearer <token>"

# Submit review decision
curl -X POST http://localhost:8000/api/v1/admin/duplicates/{case_id}/override \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "decision": "approve_duplicate",
    "justification": "Clear visual match confirmed"
  }'
```

## ⚙️ Configuration

### Environment Variables

Key configuration options (see `backend/.env.example` for complete list):

```bash
# Application
ENVIRONMENT=production
API_HOST=0.0.0.0
API_PORT=8000
WORKERS=4

# Database
MONGODB_URI=mongodb://localhost:27017/face_auth
MONGODB_DATABASE=face_auth

# Storage
STORAGE_PATH=./storage
VECTOR_DB_PATH=./storage/vector_db

# Security
JWT_SECRET_KEY=<generate-strong-key>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Face Recognition
EMBEDDING_DIMENSION=512
MIN_FACE_SIZE=80
BLUR_THRESHOLD=100.0
QUALITY_SCORE_THRESHOLD=0.5
VERIFICATION_THRESHOLD=0.85

# Performance
CACHE_DEFAULT_TTL=3600
FAISS_USE_IVF=true
FAISS_NLIST=100
FAISS_NPROBE=10
```

## 🔒 Security

- **Encryption**: AES-256 for data at rest, TLS 1.2+ for data in transit
- **Authentication**: JWT-based with configurable expiration
- **Authorization**: Role-based access control (Admin, Reviewer, User)
- **Rate Limiting**: Configurable per-endpoint rate limits
- **Audit Logging**: Comprehensive audit trail for all operations
- **Input Validation**: Pydantic models with strict validation
- **Security Headers**: X-Frame-Options, X-Content-Type-Options, etc.

## 📊 Monitoring

### Logs

Logs are stored in `logs/` directory:

- `app_YYYY-MM-DD.log` - Human-readable logs
- `app_YYYY-MM-DD.json` - Structured JSON logs

### Metrics

Access metrics at:

- `GET /api/v1/monitoring/metrics` - System metrics
- `GET /api/v1/monitoring/performance` - Performance metrics

### Health Checks

- `/health` - Basic health check (200 = healthy, 503 = unhealthy)
- `/live` - Liveness probe (always returns 200 if app is running)
- `/ready` - Readiness probe (checks all dependencies)

## 🚀 Deployment

### Docker Deployment

All deployment commands should be run from the **project root**:

```bash
# Build and start all services
docker-compose up -d

# Scale backend workers
docker-compose up -d --scale app=3

# View backend logs
docker-compose logs -f app

# View all logs
make logs
```

### Production Deployment

See detailed guides in `backend/docs/deployment/`:

- `horizontal-scaling.md` - Multi-server deployment
- `load-balancing-guide.md` - Nginx/HAProxy configuration

For backend-specific deployment details, see `backend/README.md`.

### Cloud Deployment

Kubernetes deployment example:

```bash
# Apply deployment
kubectl apply -f k8s/deployment.yaml

# Check status
kubectl get pods -l app=face-auth-api

# View logs
kubectl logs -f deployment/face-auth-api
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test categories
pytest tests/test_cache_service.py -v
pytest tests/test_batch_processing.py -v
```

## 📈 Performance

### Benchmarks

- **Application Processing**: 100+ applications/second (single worker)
- **Face Recognition**: 60+ images/second (batch processing)
- **Duplicate Detection**: 200+ searches/second (IVF index)
- **Batch Operations**: 25x faster than individual operations

### Optimization Features

- **Database**: Compound indexes, connection pooling, in-memory caching
- **Vector Search**: FAISS IVF index for 5-10x faster search
- **Batch Processing**: Bulk inserts, parallel processing
- **Horizontal Scaling**: Stateless design, load balancing support

## 🛠️ Development

### Adding New Backend Features

1. Navigate to `backend/` directory
2. Define models in `app/models/`
3. Implement business logic in `app/services/`
4. Create API endpoints in `app/api/v1/`
5. Add tests in `tests/`
6. Update documentation

For detailed development instructions, see [`backend/README.md`](backend/README.md).

### Code Style

```bash
# From backend directory
cd backend

# Format code
black app/ tests/

# Lint code
flake8 app/ tests/

# Type checking
mypy app/
```

## 📖 Documentation

### API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Project Documentation

#### Backend

- **Backend Setup**: [`backend/README.md`](backend/README.md) - Backend-specific documentation
- **Security Guide**: [`backend/docs/SECURITY.md`](backend/docs/SECURITY.md)
- **HTTPS Setup**: [`backend/docs/HTTPS_CONFIGURATION.md`](backend/docs/HTTPS_CONFIGURATION.md)
- **Deployment Guides**: [`backend/docs/deployment/`](backend/docs/deployment/)
- **Load Balancing**: [`backend/docs/deployment/load-balancing-guide.md`](backend/docs/deployment/load-balancing-guide.md)

#### Frontend & Integration

- **Integration Guide**: [`INTEGRATION_GUIDE.md`](INTEGRATION_GUIDE.md) - Frontend-backend integration
- **Error Handling**: [`ERROR_HANDLING_GUIDE.md`](ERROR_HANDLING_GUIDE.md) - Error handling and loading states
- **Testing Guide**: [`TESTING_GUIDE.md`](TESTING_GUIDE.md) - Testing setup and best practices

## 🐛 Troubleshooting

### Common Issues

**MongoDB Connection Failed**

```bash
# Check MongoDB is running (from project root)
docker-compose ps mongodb

# Check connection string in backend/.env
cat backend/.env | grep MONGODB_URI

# Restart MongoDB
docker-compose restart mongodb
```

**Port Already in Use**

```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or change port in docker-compose.yml
```

**Storage Permission Issues**

```bash
# Fix permissions (from project root)
chmod -R 755 backend/storage/
chown -R $USER:$USER backend/storage/
```

**Backend-Specific Issues**

For backend-specific troubleshooting, see the troubleshooting section in [`backend/README.md`](backend/README.md).

## 📝 License

[Your License Here]

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

## 📧 Support

For issues and questions:

- GitHub Issues: [Your Repository]
- Email: [Your Contact]
- Documentation: [Your Docs URL]

## 🙏 Acknowledgments

- FaceNet implementation: [facenet-pytorch](https://github.com/timesler/facenet-pytorch)
- FAISS: [Facebook AI Similarity Search](https://github.com/facebookresearch/faiss)
- FastAPI: [FastAPI Framework](https://fastapi.tiangolo.com/)
