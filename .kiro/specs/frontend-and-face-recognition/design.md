# Design Document

## Overview

This design document outlines the architecture and implementation approach for completing the Face Authentication and De-duplication System with a React-based frontend and full face recognition capabilities. The system will be organized with clear separation between backend (FastAPI) and frontend (React) codebases, communicating via REST APIs and WebSockets.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React + TypeScript)            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Dashboard   │  │  Upload UI   │  │  Identity    │      │
│  │  Component   │  │  Component   │  │  Management  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                            │                                 │
│                   ┌────────▼────────┐                        │
│                   │   API Client    │                        │
│                   │  (Axios/Fetch)  │                        │
│                   └────────┬────────┘                        │
└────────────────────────────┼──────────────────────────────────┘
                             │ HTTP/WebSocket
┌────────────────────────────▼──────────────────────────────────┐
│                Backend (FastAPI + Python)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │   API        │  │  Face        │  │  Duplicate   │        │
│  │  Endpoints   │  │  Recognition │  │  Detection   │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│         │                  │                  │                │
│         └──────────────────┴──────────────────┘                │
│                            │                                   │
│                   ┌────────▼────────┐                          │
│                   │    MongoDB      │                          │
│                   │   + Vector DB   │                          │
│                   └─────────────────┘                          │
└────────────────────────────────────────────────────────────────┘
```

### Project Structure

```
IndiaAIProject/
├── app/                          # Backend (existing)
│   ├── api/
│   ├── services/
│   ├── models/
│   └── main.py
├── frontend/                     # New frontend directory
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── hooks/
│   │   ├── types/
│   │   ├── utils/
│   │   └── App.tsx
│   ├── package.json
│   └── tsconfig.json
├── storage/
├── scripts/
└── requirements.txt
```

## Components and Interfaces

### Frontend Components

#### 1. Authentication Components

**LoginPage Component**

- Form with username/password inputs
- Submit button with loading state
- Error message display
- Redirect logic after successful login

**ProtectedRoute Component**

- Wrapper for authenticated routes
- Checks for valid JWT token
- Redirects to login if unauthenticated

#### 2. Dashboard Components

**DashboardPage Component**

- Statistics cards (applications, identities, duplicates)
- Charts for trends (applications over time)
- Recent applications table
- System health indicators

**StatCard Component**

- Displays a single metric with icon
- Shows trend indicator (up/down)
- Clickable to navigate to detail view

#### 3. Application Management Components

**UploadPage Component**

- Drag-and-drop file upload zone
- Image preview before submission
- Form for additional metadata
- Real-time processing status display

**ApplicationList Component**

- Paginated table of applications
- Filters by status, date range
- Search by application ID
- Click to view details

**ApplicationDetail Component**

- Full application information
- Uploaded photograph display
- Processing results
- Match visualization if duplicate detected

#### 4. Identity Management Components

**IdentityList Component**

- Grid or list view of identities
- Search and filter capabilities
- Pagination controls
- Click to view identity details

**IdentityDetail Component**

- Identity information display
- Gallery of associated photographs
- Application history timeline
- Actions (flag, merge, delete)

#### 5. Admin Components

**AdminPanel Component**

- User management table
- System health dashboard
- Circuit breaker controls
- Audit log viewer

### Backend Components

#### 1. Face Recognition Service

**FaceDetectionService**

```python
class FaceDetectionService:
    def detect_faces(self, image_path: str) -> List[FaceDetection]
    def extract_face_region(self, image: np.ndarray, bbox: BoundingBox) -> np.ndarray
    def assess_face_quality(self, face_image: np.ndarray) -> QualityScore
```

**FaceEmbeddingService**

```python
class FaceEmbeddingService:
    def __init__(self, model_name: str = "facenet")
    def generate_embedding(self, face_image: np.ndarray) -> np.ndarray
    def normalize_embedding(self, embedding: np.ndarray) -> np.ndarray
```

**DuplicateDetectionService**

```python
class DuplicateDetectionService:
    def find_matches(self, embedding: np.ndarray, threshold: float = 0.85) -> List[Match]
    def calculate_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float
    def rank_matches(self, matches: List[Match]) -> List[Match]
```

#### 2. Image Processing Service

**ImageQualityService**

```python
class ImageQualityService:
    def check_resolution(self, image: np.ndarray) -> bool
    def detect_blur(self, image: np.ndarray) -> float
    def assess_lighting(self, image: np.ndarray) -> float
    def calculate_quality_score(self, image: np.ndarray) -> QualityScore
```

#### 3. WebSocket Manager

**WebSocketManager**

```python
class WebSocketManager:
    def connect(self, client_id: str, websocket: WebSocket)
    def disconnect(self, client_id: str)
    def send_update(self, client_id: str, message: dict)
    def broadcast(self, message: dict)
```

### API Endpoints

#### New Endpoints

**Face Recognition Endpoints**

```
POST   /api/v1/face/detect          - Detect faces in image
POST   /api/v1/face/embed            - Generate face embedding
POST   /api/v1/face/compare          - Compare two face embeddings
```

**WebSocket Endpoint**

```
WS     /api/v1/ws/{client_id}        - WebSocket for real-time updates
```

**Frontend Serving**

```
GET    /*                            - Serve React frontend (catch-all)
```

## Data Models

### Frontend TypeScript Interfaces

```typescript
interface Application {
  application_id: string;
  identity_id?: string;
  status: "pending" | "processing" | "completed" | "failed";
  created_at: string;
  processing?: ProcessingInfo;
  result?: ProcessingResult;
}

interface ProcessingResult {
  is_duplicate: boolean;
  confidence_score: number;
  identity_id?: string;
  match_details?: MatchDetails;
}

interface Identity {
  unique_id: string;
  status: "active" | "flagged" | "merged";
  created_at: string;
  photographs: string[];
  application_count: number;
}

interface FaceDetection {
  bbox: BoundingBox;
  confidence: number;
  landmarks?: FaceLandmarks;
}

interface QualityScore {
  overall: number;
  blur_score: number;
  lighting_score: number;
  face_size_score: number;
}
```

### Backend Models

**FaceEmbedding Model** (new)

```python
class FaceEmbedding(BaseModel):
    application_id: str
    identity_id: Optional[str]
    embedding: List[float]  # 512-dimensional vector
    model_version: str
    created_at: datetime
```

**FaceDetectionResult Model** (new)

```python
class FaceDetectionResult(BaseModel):
    bbox: BoundingBox
    confidence: float
    landmarks: Optional[Dict[str, Tuple[int, int]]]
    quality_score: QualityScore
```

## Error Handling

### Frontend Error Handling

1. **API Errors**: Display user-friendly error messages with retry options
2. **Network Errors**: Show offline indicator and queue requests
3. **Validation Errors**: Inline form validation with clear messages
4. **Authentication Errors**: Automatic token refresh, redirect to login if expired

### Backend Error Handling

1. **Face Detection Failures**: Return specific error codes (NO_FACE_DETECTED, MULTIPLE_FACES, POOR_QUALITY)
2. **Model Loading Errors**: Graceful degradation with error logging
3. **Database Errors**: Retry logic with exponential backoff
4. **WebSocket Errors**: Automatic reconnection with connection state management

## Testing Strategy

### Frontend Testing

1. **Unit Tests**: Jest + React Testing Library for components
2. **Integration Tests**: Test API client interactions
3. **E2E Tests**: Cypress for critical user flows
4. **Visual Regression**: Chromatic or Percy for UI consistency

### Backend Testing

1. **Unit Tests**: Pytest for services and utilities
2. **Integration Tests**: Test face recognition pipeline end-to-end
3. **API Tests**: Test all endpoints with various scenarios
4. **Performance Tests**: Load testing for face recognition operations

## Technology Stack

### Frontend

- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Routing**: React Router v6
- **State Management**: Zustand or React Context
- **UI Library**: Material-UI (MUI) or Ant Design
- **HTTP Client**: Axios
- **WebSocket**: native WebSocket API or socket.io-client
- **Charts**: Recharts or Chart.js
- **Form Handling**: React Hook Form
- **Styling**: Tailwind CSS or styled-components

### Backend (New Dependencies)

- **Face Recognition**: face_recognition library (dlib-based) or DeepFace
- **Image Processing**: OpenCV (cv2), Pillow
- **Vector Operations**: NumPy, SciPy
- **WebSocket**: FastAPI WebSocket support
- **Model Storage**: Download and cache pre-trained models

## Deployment Considerations

### Development Setup

1. Backend runs on `http://localhost:8000`
2. Frontend dev server runs on `http://localhost:5173` (Vite default)
3. Frontend proxies API requests to backend
4. CORS configured for local development

### Production Setup

1. Frontend built as static files
2. FastAPI serves frontend static files
3. Single deployment artifact (Docker container)
4. Environment-based configuration
5. CDN for static assets (optional)

## Security Considerations

1. **File Upload**: Validate file types, scan for malware, limit file sizes
2. **Image Storage**: Secure file permissions, encrypted storage
3. **API Authentication**: JWT tokens with short expiration
4. **WebSocket Security**: Authenticate WebSocket connections
5. **XSS Prevention**: Sanitize user inputs, use Content Security Policy
6. **CSRF Protection**: CSRF tokens for state-changing operations

## Performance Optimizations

### Frontend

1. **Code Splitting**: Lazy load routes and components
2. **Image Optimization**: Compress and resize images before upload
3. **Caching**: Cache API responses with React Query or SWR
4. **Virtual Scrolling**: For large lists of applications/identities
5. **Debouncing**: Debounce search and filter inputs

### Backend

1. **Model Caching**: Load face recognition models once at startup
2. **Batch Processing**: Process multiple faces in batches
3. **Async Operations**: Use async/await for I/O operations
4. **Connection Pooling**: Optimize database connections
5. **CDN**: Serve static assets from CDN

## Face Recognition Implementation Details

### Model Selection

**Primary Option: face_recognition library**

- Based on dlib's state-of-the-art face recognition
- 99.38% accuracy on Labeled Faces in the Wild benchmark
- Generates 128-dimensional embeddings
- Easy to use Python API

**Alternative: DeepFace**

- Supports multiple models (VGG-Face, Facenet, OpenFace, DeepID, ArcFace)
- More flexible but heavier
- Better for experimentation

### Face Detection Pipeline

1. **Load Image**: Read image file from storage
2. **Detect Faces**: Use HOG or CNN-based detector
3. **Extract Face**: Crop face region with padding
4. **Align Face**: Normalize face orientation using landmarks
5. **Generate Embedding**: Pass through neural network
6. **Store Embedding**: Save to database with metadata

### Similarity Calculation

```python
def calculate_similarity(embedding1, embedding2):
    # Cosine similarity
    dot_product = np.dot(embedding1, embedding2)
    norm1 = np.linalg.norm(embedding1)
    norm2 = np.linalg.norm(embedding2)
    similarity = dot_product / (norm1 * norm2)
    return similarity
```

### Threshold Tuning

- **High Confidence (>0.90)**: Definite match
- **Medium Confidence (0.85-0.90)**: Likely match, manual review recommended
- **Low Confidence (<0.85)**: Different person

## Real-time Updates Flow

1. Client uploads image
2. Server creates application record
3. Server establishes WebSocket connection
4. Server processes image asynchronously
5. Server sends progress updates via WebSocket:
   - "Face detection started"
   - "Face detected"
   - "Generating embedding"
   - "Comparing with existing identities"
   - "Processing complete"
6. Client displays updates in real-time
7. Final result sent via WebSocket and HTTP response

## Migration and Data Seeding

1. Add face recognition dependencies to requirements.txt
2. Download pre-trained models on first run
3. Create migration script to process existing photographs
4. Generate embeddings for seeded data
5. Update database schema for embeddings collection
