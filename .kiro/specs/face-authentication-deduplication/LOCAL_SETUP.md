# Local Development Setup Guide

## Overview

This guide outlines the local development setup for the Face Authentication and De-duplication System using free and open-source tools.

## Technology Stack (Local Development)

### Core Technologies

- **Backend**: Python 3.9+ with FastAPI
- **Database**: MongoDB Atlas (free tier) or local MongoDB
- **Vector Search**: FAISS (free, CPU-based, local library)
- **Face Recognition**: facenet-pytorch or DeepFace (free, open-source)
- **Caching**: Redis (optional, via Docker)
- **Storage**: Local file system

### Key Libraries

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pymongo==4.6.0
pydantic==2.5.0
python-dotenv==1.0.0
facenet-pytorch==2.5.3
torch==2.1.0
torchvision==0.16.0
opencv-python==4.8.1
numpy==1.24.3
faiss-cpu==1.7.4
Pillow==10.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
slowapi==0.1.9
```

## Environment Setup

### 1. MongoDB Configuration

**Option A: MongoDB Atlas (Recommended for Development)**

```bash
# Use the provided connection string
MONGODB_URI=mongodb+srv://gkt2work_db_user:a0T824d9ek4rA9ou@cluster0.cmae5by.mongodb.net/face_auth_db
```

**Option B: Local MongoDB via Docker**

```bash
docker run -d -p 27017:27017 --name mongodb mongo:7
MONGODB_URI=mongodb://localhost:27017/face_auth_db
```

### 2. Redis Setup (Optional)

```bash
docker run -d -p 6379:6379 --name redis redis:7-alpine
```

### 3. Environment Variables (.env)

```bash
# Database
MONGODB_URI=mongodb+srv://gkt2work_db_user:a0T824d9ek4rA9ou@cluster0.cmae5by.mongodb.net/face_auth_db

# Storage
STORAGE_PATH=./storage/photographs
VECTOR_DB_PATH=./storage/vectors

# Vector Database
VECTOR_DB_TYPE=faiss

# Face Recognition
FACE_MODEL=facenet  # or deepface

# Redis (optional)
REDIS_URL=redis://localhost:6379

# Security
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60

# API
API_HOST=0.0.0.0
API_PORT=8000
```

### 4. Directory Structure

```
face-authentication-deduplication/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Configuration management
│   ├── models/                 # Pydantic models
│   │   ├── application.py
│   │   ├── identity.py
│   │   └── audit_log.py
│   ├── services/               # Business logic
│   │   ├── ingestion.py
│   │   ├── face_recognition.py
│   │   ├── deduplication.py
│   │   ├── identity_management.py
│   │   └── review.py
│   ├── database/               # Database operations
│   │   ├── mongodb.py
│   │   └── faiss_index.py
│   ├── api/                    # API routes
│   │   ├── applications.py
│   │   ├── admin.py
│   │   └── auth.py
│   └── utils/                  # Utilities
│       ├── security.py
│       ├── logging.py
│       └── validators.py
├── storage/
│   ├── photographs/            # Uploaded photos
│   └── vectors/                # FAISS index files
├── tests/
│   ├── test_face_recognition.py
│   ├── test_deduplication.py
│   └── test_api.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env
└── README.md
```

## Running Locally

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Create Storage Directories

```bash
mkdir -p storage/photographs
mkdir -p storage/vectors
```

### 3. Start Services (Optional)

```bash
# Start Redis (if using)
docker-compose up -d redis
```

### 4. Run the Application

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode with multiple workers
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 5. Access the API

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Admin Dashboard**: http://localhost:8000/admin (if implemented)

## Testing the System

### Submit an Application

```bash
curl -X POST "http://localhost:8000/api/v1/applications" \
  -H "Content-Type: multipart/form-data" \
  -F "photograph=@test_photo.jpg" \
  -F "applicant_data={\"name\":\"John Doe\",\"email\":\"john@example.com\"}"
```

### Check Application Status

```bash
curl "http://localhost:8000/api/v1/applications/{application_id}/status"
```

### Admin Login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

## Free APIs and Services

### Face Recognition Models

- **facenet-pytorch**: Free, open-source, runs locally
- **DeepFace**: Free, open-source, supports multiple models
- **MTCNN**: Free face detection model

### Vector Database

- **FAISS**: Free, open-source, CPU-based (no GPU required)
- **Qdrant**: Free, self-hosted option available

### Storage

- **Local File System**: Free, no external dependencies
- **MinIO**: Free, S3-compatible, self-hosted (for future)

### Monitoring

- **FastAPI Built-in Metrics**: Free
- **Python Logging**: Free
- **Simple HTML Dashboard**: Free, no external services

## Performance Expectations (Local Development)

- **Face Detection**: ~100-200ms per image (CPU)
- **Embedding Generation**: ~200-300ms per image (CPU)
- **FAISS Search**: ~10-50ms for 10K embeddings (CPU)
- **Total Processing Time**: ~500ms - 1s per application (CPU)

## Scaling to Production

When ready for production:

1. **Database**: Continue with MongoDB Atlas (paid tiers for more storage)
2. **Vector Database**: Consider Qdrant Cloud or Pinecone (paid)
3. **Storage**: Migrate to AWS S3, Google Cloud Storage, or Azure Blob
4. **Compute**: Deploy to AWS EC2, Google Cloud Run, or Azure App Service
5. **GPU Acceleration**: Use cloud GPU instances for faster processing

## Troubleshooting

### MongoDB Connection Issues

- Check network connectivity to MongoDB Atlas
- Verify IP whitelist in MongoDB Atlas (allow 0.0.0.0/0 for development)
- Test connection using MongoDB Compass

### FAISS Index Issues

- Ensure storage/vectors directory exists and is writable
- Check disk space for index files
- Verify numpy and faiss-cpu versions are compatible

### Face Detection Failures

- Verify image format (JPEG/PNG)
- Check image resolution (minimum 300x300px)
- Ensure face is clearly visible and well-lit

### Performance Issues

- Use FAISS IndexIVFFlat instead of IndexFlatL2 for large datasets
- Enable batch processing for multiple applications
- Consider using Redis for caching embeddings
- Use multiple uvicorn workers for parallel processing

## Next Steps

1. Complete Task 1: Set up project structure
2. Complete Task 2: Implement MongoDB models
3. Complete Task 3: Build Application Ingestion Service
4. Continue with remaining tasks sequentially

Once local development is stable and tested, plan for production deployment with appropriate cloud services and scaling strategies.
