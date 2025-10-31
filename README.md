# Face Authentication and De-duplication System

AI-powered face authentication system for large-scale public examinations in India. This system prevents duplicate registrations and verifies applicant identities through advanced facial recognition technology.

## Features

- **Automated De-duplication**: Detect duplicate applications using facial recognition
- **Unique Identity Management**: Assign single unique IDs to verified applicants
- **High Performance**: Process 10,000+ applications per hour
- **Secure**: AES-256 encryption, role-based access control, comprehensive audit logging
- **Scalable**: Horizontal scaling support with efficient vector search

## Technology Stack

- **Backend**: FastAPI (Python)
- **Database**: MongoDB (Atlas)
- **Vector Database**: FAISS
- **Cache**: Redis
- **Face Recognition**: FaceNet (facenet-pytorch)
- **Logging**: Loguru

## Project Structure

```
.
├── app/
│   ├── api/              # API routes and endpoints
│   │   └── v1/           # API version 1
│   ├── core/             # Core configuration and logging
│   ├── database/         # Database connections and operations
│   ├── models/           # Data models and schemas
│   ├── services/         # Business logic services
│   └── utils/            # Utility functions
├── storage/
│   ├── photographs/      # Applicant photographs
│   └── vectors/          # FAISS vector index
├── tests/                # Test suite
├── logs/                 # Application logs
├── docker-compose.yml    # Docker services configuration
├── requirements.txt      # Python dependencies
└── .env                  # Environment variables
```

## Setup Instructions

### Prerequisites

- Python 3.10+
- Docker and Docker Compose
- MongoDB Atlas account (or local MongoDB)

### Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd face-authentication-deduplication
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set up environment variables:

```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Start Redis (and optional MongoDB):

```bash
docker-compose up -d
```

6. Create storage directories (if not exists):

```bash
mkdir -p storage/photographs storage/vectors logs
```

### Running the Application

Start the development server:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:

- API: http://localhost:8000
- Interactive API docs: http://localhost:8000/docs
- Alternative API docs: http://localhost:8000/redoc

### Running Tests

```bash
pytest tests/ -v
```

## API Endpoints

### Health Checks

- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /ready` - Readiness check

### Application Management (Coming Soon)

- `POST /api/v1/applications` - Submit new application
- `GET /api/v1/applications/{id}/status` - Check application status

### Admin Endpoints (Coming Soon)

- `GET /api/v1/admin/duplicates` - List duplicate cases
- `POST /api/v1/admin/duplicates/{caseId}/override` - Override duplicate decision

## Configuration

Key environment variables:

- `MONGODB_URI`: MongoDB connection string
- `REDIS_URL`: Redis connection URL
- `VERIFICATION_THRESHOLD`: Face matching threshold (default: 0.85)
- `LOG_LEVEL`: Logging level (INFO, DEBUG, WARNING, ERROR)
- `SECRET_KEY`: JWT secret key for authentication

See `.env.example` for complete configuration options.

## Development

### Code Structure

- **app/core**: Configuration, logging, and core utilities
- **app/models**: Pydantic models for data validation
- **app/services**: Business logic (face recognition, de-duplication, identity management)
- **app/database**: Database connections and operations
- **app/api**: REST API endpoints

### Adding New Features

1. Define models in `app/models/`
2. Implement business logic in `app/services/`
3. Create API endpoints in `app/api/v1/`
4. Add tests in `tests/`

## Monitoring

Logs are stored in:

- `logs/app_YYYY-MM-DD.log` - Human-readable logs
- `logs/app_YYYY-MM-DD.json` - Structured JSON logs

## Security

- All sensitive data encrypted at rest and in transit
- JWT-based authentication
- Role-based access control
- Comprehensive audit logging
- Rate limiting on API endpoints

## License

[Your License Here]

## Support

For issues and questions, please contact [Your Contact Information]
