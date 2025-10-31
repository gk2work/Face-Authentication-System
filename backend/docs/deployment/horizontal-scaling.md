# Horizontal Scaling Configuration

This document describes how to configure the Face Authentication and De-duplication System for horizontal scaling across multiple worker processes and servers.

## Stateless Design

The application is designed to be stateless, with all state stored in external services:

- **MongoDB**: All application data, identities, and audit logs
- **FAISS Vector Index**: Stored on disk and loaded by each worker
- **In-Memory Cache**: Each worker maintains its own cache (eventual consistency)

### Important Note: Queue Service

The current implementation uses an in-memory queue service for development. For production horizontal scaling, you should:

1. **Replace with a distributed queue** (e.g., RabbitMQ, Redis Queue, AWS SQS)
2. **Use a message broker** to distribute work across workers
3. **Implement proper job distribution** to avoid duplicate processing

Example migration to Redis Queue:

```python
# Replace app/services/queue_service.py with Redis-based implementation
import redis
from rq import Queue

redis_conn = redis.Redis(host='redis-host', port=6379)
queue = Queue(connection=redis_conn)
```

Until migrated, the in-memory queue will only work within a single process/worker.

## Multi-Worker Configuration

### Uvicorn Workers

Run the application with multiple worker processes using uvicorn:

```bash
# Single server with 4 workers
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Or using gunicorn with uvicorn workers
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
```

### Worker Count Recommendations

- **CPU-bound workloads**: `workers = (2 * CPU_cores) + 1`
- **I/O-bound workloads**: `workers = (4 * CPU_cores)`
- **Face recognition workloads**: `workers = CPU_cores` (due to ML model memory)

For a 4-core server:

- Recommended: 4-8 workers
- Maximum: 16 workers (monitor memory usage)

## Load Balancing

### Nginx Configuration

```nginx
upstream face_auth_backend {
    # Round-robin load balancing
    server 10.0.1.10:8000;
    server 10.0.1.11:8000;
    server 10.0.1.12:8000;

    # Health check
    keepalive 32;
}

server {
    listen 80;
    server_name api.faceauth.example.com;

    location / {
        proxy_pass http://face_auth_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts for long-running requests
        proxy_connect_timeout 60s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }

    location /health {
        proxy_pass http://face_auth_backend/health;
        access_log off;
    }
}
```

### HAProxy Configuration

```haproxy
frontend face_auth_frontend
    bind *:80
    mode http
    default_backend face_auth_backend

backend face_auth_backend
    mode http
    balance roundrobin
    option httpchk GET /health

    server worker1 10.0.1.10:8000 check inter 5s fall 3 rise 2
    server worker2 10.0.1.11:8000 check inter 5s fall 3 rise 2
    server worker3 10.0.1.12:8000 check inter 5s fall 3 rise 2
```

## Shared Storage Considerations

### FAISS Vector Index

The FAISS index is stored on disk and loaded by each worker. For horizontal scaling:

**Option 1: Shared Network Storage (NFS/EFS)**

```bash
# Mount shared storage on all workers
mount -t nfs 10.0.1.100:/shared/vector_db /app/storage/vector_db
```

**Option 2: Periodic Sync**

```bash
# Sync index from primary to workers every 5 minutes
*/5 * * * * rsync -avz primary:/app/storage/vector_db/ /app/storage/vector_db/
```

**Option 3: Centralized Vector Service**

- Deploy a dedicated vector search service (e.g., Milvus, Weaviate)
- All workers query the centralized service

### MongoDB Connection Pooling

Each worker maintains its own connection pool to MongoDB:

```python
# app/database/mongodb.py
AsyncIOMotorClient(
    settings.MONGODB_URI,
    maxPoolSize=50,  # Per worker
    minPoolSize=10,
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=10000,
    retryWrites=True,
)
```

**Total connections** = `workers * maxPoolSize`

- 4 workers × 50 = 200 connections
- Ensure MongoDB can handle the total connection count

## Environment Variables

Set these environment variables for production deployment:

```bash
# Application
ENVIRONMENT=production
API_HOST=0.0.0.0
API_PORT=8000

# MongoDB
MONGODB_URI=mongodb://user:pass@mongodb-cluster:27017/face_auth?replicaSet=rs0
MONGODB_DATABASE=face_auth

# Storage (use shared storage path)
STORAGE_PATH=/shared/storage
VECTOR_DB_PATH=/shared/vector_db

# Security
JWT_SECRET_KEY=<strong-random-key>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Performance
WORKERS=4  # Number of uvicorn workers
```

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/

# Create storage directories
RUN mkdir -p /app/storage/photographs /app/storage/vector_db

# Expose port
EXPOSE 8000

# Run with multiple workers
CMD ["gunicorn", "app.main:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120"]
```

### Docker Compose (Multi-Container)

```yaml
version: "3.8"

services:
  face-auth-api-1:
    build: .
    environment:
      - MONGODB_URI=mongodb://mongodb:27017/face_auth
      - WORKERS=2
    volumes:
      - shared-storage:/app/storage
    depends_on:
      - mongodb
    networks:
      - face-auth-network

  face-auth-api-2:
    build: .
    environment:
      - MONGODB_URI=mongodb://mongodb:27017/face_auth
      - WORKERS=2
    volumes:
      - shared-storage:/app/storage
    depends_on:
      - mongodb
    networks:
      - face-auth-network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - face-auth-api-1
      - face-auth-api-2
    networks:
      - face-auth-network

  mongodb:
    image: mongo:6
    volumes:
      - mongodb-data:/data/db
    networks:
      - face-auth-network

volumes:
  shared-storage:
  mongodb-data:

networks:
  face-auth-network:
```

## Kubernetes Deployment

### Deployment YAML

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: face-auth-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: face-auth-api
  template:
    metadata:
      labels:
        app: face-auth-api
    spec:
      containers:
        - name: api
          image: face-auth-api:latest
          ports:
            - containerPort: 8000
          env:
            - name: MONGODB_URI
              valueFrom:
                secretKeyRef:
                  name: face-auth-secrets
                  key: mongodb-uri
            - name: WORKERS
              value: "2"
          resources:
            requests:
              memory: "2Gi"
              cpu: "1000m"
            limits:
              memory: "4Gi"
              cpu: "2000m"
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /ready
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 5
          volumeMounts:
            - name: shared-storage
              mountPath: /app/storage
      volumes:
        - name: shared-storage
          persistentVolumeClaim:
            claimName: face-auth-storage-pvc

---
apiVersion: v1
kind: Service
metadata:
  name: face-auth-api-service
spec:
  selector:
    app: face-auth-api
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: LoadBalancer
```

## Monitoring and Auto-Scaling

### Horizontal Pod Autoscaler (Kubernetes)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: face-auth-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: face-auth-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

## Performance Tuning

### Connection Pool Sizing

```python
# For N workers across M servers:
# Total MongoDB connections = N * M * maxPoolSize

# Example: 3 servers × 4 workers × 50 = 600 connections
# Ensure MongoDB can handle this load
```

### Cache Considerations

Each worker maintains its own in-memory cache:

- Cache invalidation happens per-worker
- Eventual consistency across workers
- Consider Redis for shared caching if needed

### FAISS Index Optimization

- Use IVF index for datasets > 10,000 vectors
- Adjust `nlist` and `nprobe` based on dataset size
- Consider GPU acceleration for very large datasets

## Troubleshooting

### High Memory Usage

- Reduce number of workers
- Reduce MongoDB connection pool size
- Monitor FAISS index memory usage

### Slow Response Times

- Check MongoDB query performance
- Verify FAISS index is trained (for IVF)
- Monitor network latency to shared storage

### Cache Inconsistency

- Reduce cache TTL
- Implement cache warming on startup
- Consider centralized caching (Redis)

## Best Practices

1. **Start small**: Begin with 2-4 workers per server
2. **Monitor metrics**: Track CPU, memory, and response times
3. **Load test**: Test with realistic workloads before production
4. **Gradual scaling**: Add workers/servers incrementally
5. **Health checks**: Implement robust health and readiness checks
6. **Graceful shutdown**: Handle SIGTERM for clean worker shutdown
