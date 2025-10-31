# Face Authentication and De-duplication System

An AI-powered face authentication and de-duplication system designed for large-scale public examinations in India. This system prevents duplicate registrations by using advanced facial recognition technology to perform one-to-many matching against a historical database.

## 🎯 Project Overview

This project is part of the IndiaAI Application Development Initiative (IADI), aimed at strengthening the integrity of public examination processes through AI-enabled de-duplication.

### Key Features

- **Automated Duplicate Detection**: Uses facial recognition to identify multiple applications from the same individual
- **One-to-Many Identity Verification**: Ensures each applicant receives a single unique ID
- **High Accuracy**: Targets 99.5%+ accuracy in duplicate detection
- **Scalable**: Designed to process 10,000+ applications per hour
- **Secure**: Implements encryption, authentication, and comprehensive audit logging
- **Admin Review Interface**: Allows manual review and override of flagged duplicates

## 🏗️ Architecture

- **Backend**: Python 3.9+ with FastAPI
- **Database**: MongoDB (Atlas or local)
- **Vector Search**: FAISS (CPU-based, local)
- **Face Recognition**: facenet-pytorch or DeepFace
- **Caching**: Redis (optional)
- **Storage**: Local file system (development), S3-compatible (production)

## 📋 Prerequisites

- Python 3.9 or higher
- MongoDB Atlas account (free tier) or local MongoDB
- Docker (optional, for Redis)
- 4GB+ RAM recommended
- Internet connection for model downloads

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/gk2work/Face-Authentication-System.git
cd Face-Authentication-System
```

### 2. Set Up Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Create a `.env` file in the project root:

```bash
MONGODB_URI=mongodb+srv://your-connection-string
STORAGE_PATH=./storage/photographs
VECTOR_DB_PATH=./storage/vectors
VECTOR_DB_TYPE=faiss
FACE_MODEL=facenet
JWT_SECRET_KEY=your-secret-key-change-in-production
```

### 5. Create Storage Directories

```bash
mkdir -p storage/photographs
mkdir -p storage/vectors
```

### 6. Run the Application

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Access the API

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 📚 Documentation

- [Requirements Document](.kiro/specs/face-authentication-deduplication/requirements.md)
- [Design Document](.kiro/specs/face-authentication-deduplication/design.md)
- [Implementation Tasks](.kiro/specs/face-authentication-deduplication/tasks.md)
- [Local Setup Guide](.kiro/specs/face-authentication-deduplication/LOCAL_SETUP.md)

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_face_recognition.py
```

## 📊 API Usage Examples

### Submit an Application

```bash
curl -X POST "http://localhost:8000/api/v1/applications" \
  -H "Content-Type: multipart/form-data" \
  -F "photograph=@photo.jpg" \
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

## 🔒 Security

- JWT-based authentication
- Password hashing with bcrypt
- Rate limiting on API endpoints
- Audit logging for all operations
- Secure file storage with proper permissions

## 🎯 Performance Targets

- **Processing Time**: < 5 seconds per application
- **Throughput**: 10,000+ applications per hour
- **Accuracy**: 99.5%+ duplicate detection rate
- **False Positive Rate**: < 0.1%
- **Availability**: 99.9%+ uptime

## 🛠️ Technology Stack

### Core Technologies

- **FastAPI**: Modern, fast web framework
- **PyMongo**: MongoDB driver for Python
- **FAISS**: Efficient similarity search
- **facenet-pytorch**: Face recognition models
- **OpenCV**: Image processing
- **Redis**: Caching (optional)

### Key Libraries

- pydantic: Data validation
- python-jose: JWT tokens
- passlib: Password hashing
- slowapi: Rate limiting
- uvicorn: ASGI server

## 📈 Roadmap

- [x] Requirements and design documentation
- [x] Implementation task planning
- [ ] Core API implementation
- [ ] Face recognition service
- [ ] De-duplication engine
- [ ] Admin review interface
- [ ] Testing and optimization
- [ ] Production deployment

## 🤝 Contributing

This project is part of the IndiaAI Challenge. Contributions should align with the project requirements and design specifications.

## 📄 License

This project is developed for the IndiaAI Application Development Initiative.

## 👥 Team

Developed for the IndiaAI Face Authentication Challenge.

## 📞 Support

For issues and questions, please open an issue on GitHub.

## 🙏 Acknowledgments

- IndiaAI Mission
- Digital India Corporation (DIC)
- Ministry of Electronics and IT (MeitY)

---

**Note**: This system is currently in development. For local development setup and detailed instructions, see [LOCAL_SETUP.md](.kiro/specs/face-authentication-deduplication/LOCAL_SETUP.md).
