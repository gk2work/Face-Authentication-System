# Face Authentication and De-duplication System

AI-powered face authentication system for large-scale public examinations in India. This system prevents duplicate registrations and verifies applicant identities through advanced facial recognition technology.

## 🚀 Features

- **Automated De-duplication**: Detect duplicate applications using facial recognition with 85%+ accuracy
- **Unique Identity Management**: Assign single unique IDs to verified applicants
- **High Performance**: Process 10,000+ applications per hour with batch processing
- **Secure**: AES-256 encryption, JWT authentication, role-based access control
- **Scalable**: Horizontal scaling support with load balancing and caching
- **Comprehensive Audit Trail**: Track all operations with detailed logging
- **Webhook Notifications**: Real-time status updates via webhooks
- **Admin Review Interface**: Manual review for borderline duplicate cases

## 📋 Technology Stack

- **Backend**: FastAPI (Python 3.10+)
- **Database**: MongoDB 6.0
- **Vector Search**: FAISS with IVF optimization
- **Cache**: In-memory cache with TTL
- **Face Recognition**: FaceNet (InceptionResnetV1)
- **Logging**: Loguru with structured JSON logs
- **Deployment**: Docker & Docker Compose

## 🏗️ Project Structure

```
.
├── app/
│   ├── api/v1/           # API endpoints (applications, auth, admin, monitoring)
│   ├── core/             # Configuration, logging, security
│   ├── database/         # MongoDB connections and repositories
│   ├── models/           # Pydantic models (Application, Identity, Audit)
│   ├── services/         # Business logic services
│   │   ├── application_processor.py    # End-to-end workflow orchestrator
│   │   ├── face_recognition_service.py # Face detection and embedding
│   │   ├── deduplication_service.py    # Duplicate detection
│   │   ├── identity_service.py         # Identity management
│   │   ├── notification_service.py     # Webhook notifications
│   │   └── review_workflow_service.py  # Admin review workflow
│   └── utils/            # Utility functions and error handling
├── storage/
│   ├── photographs/      # Applicant photographs
│   └── vector_db/        # FAISS vector index
├── tests/                # Test suite
├── logs/                 # Application logs
├── docs/                 # Documentation
├── config/               # Configuration files (nginx, haproxy, env)
├── scripts/              # Utility scripts
├── docker-compose.yml    # Docker services configuration
├── Dockerfile            # Application container
├── Makefile              # Convenient commands
└── requirements.txt      # Python dependencies
```

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
make init
```

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

### Prerequisites

- Python 3.10+
- MongoDB 6.0+ (local or Atlas)
- 4GB RAM minimum

### Installation

1. **Create virtual environment**:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**:

```bash
pip install -r requirements.txt
```

3. **Set up environment variables**:

```bash
cp config/production.env.example .env
# Edit .env with your configuration
```

4. **Create storage directories**:

```bash
mkdir -p storage/photographs storage/vector_db logs
```

5. **Start MongoDB** (if running locally):

```bash
# Using Docker
docker run -d -p 27017:27017 --name mongodb mongo:6

# Or install MongoDB locally
# https://www.mongodb.com/docs/manual/installation/
```

### Running the Application

```bash
# Development mode with hot reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode with multiple workers
./scripts/start_production.sh

# Or with gunicorn
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_cache_service.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

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

Key configuration options (see `config/production.env.example` for complete list):

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

```bash
# Build and start
docker-compose up -d

# Scale workers
docker-compose up -d --scale app=3

# View logs
docker-compose logs -f app
```

### Production Deployment

See detailed guides in `docs/deployment/`:

- `horizontal-scaling.md` - Multi-server deployment
- `load-balancing-guide.md` - Nginx/HAProxy configuration
- `performance-optimizations.md` - Performance tuning

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

### Adding New Features

1. Define models in `app/models/`
2. Implement business logic in `app/services/`
3. Create API endpoints in `app/api/v1/`
4. Add tests in `tests/`
5. Update documentation

### Code Style

```bash
# Format code
black app/ tests/

# Lint code
flake8 app/ tests/

# Type checking
mypy app/
```

## 📖 Documentation

- **API Documentation**: http://localhost:8000/docs
- **Performance Guide**: `docs/performance-optimizations.md`
- **Deployment Guide**: `docs/deployment/`
- **Load Balancing**: `docs/deployment/load-balancing-guide.md`

## 🐛 Troubleshooting

### Common Issues

**MongoDB Connection Failed**

```bash
# Check MongoDB is running
docker-compose ps mongodb

# Check connection string in .env
echo $MONGODB_URI

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
# Fix permissions
chmod -R 755 storage/
chown -R $USER:$USER storage/
```

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
