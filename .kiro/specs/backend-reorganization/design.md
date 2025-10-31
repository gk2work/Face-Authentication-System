# Design Document

## Overview

This design outlines the approach for reorganizing the Face Authentication and De-duplication System from a backend-only root-level structure to a monorepo structure with a dedicated `backend/` directory. This reorganization prepares the project for frontend integration while maintaining all existing backend functionality.

## Architecture

### Current Structure

```
.
├── app/                    # FastAPI application
├── tests/                  # Test suite
├── storage/                # Data storage
├── logs/                   # Application logs
├── config/                 # Configuration files
├── scripts/                # Utility scripts
├── docs/                   # Documentation
├── docker-compose.yml      # Docker orchestration
├── Dockerfile              # Backend container
├── requirements.txt        # Python dependencies
├── Makefile               # Build commands
└── README.md              # Documentation
```

### Target Structure

```
.
├── backend/               # Backend directory (NEW)
│   ├── app/              # FastAPI application (MOVED)
│   ├── tests/            # Test suite (MOVED)
│   ├── storage/          # Data storage (MOVED)
│   ├── logs/             # Application logs (MOVED)
│   ├── config/           # Configuration files (MOVED)
│   ├── scripts/          # Utility scripts (MOVED)
│   ├── docs/             # Backend docs (MOVED)
│   ├── Dockerfile        # Backend container (MOVED)
│   ├── requirements.txt  # Python dependencies (MOVED)
│   ├── Makefile          # Backend commands (MOVED)
│   ├── .env              # Environment config (MOVED)
│   ├── .env.example      # Env template (MOVED)
│   └── README.md         # Backend-specific docs (NEW)
├── docker-compose.yml    # Orchestration (UPDATED)
├── .gitignore           # Git ignore (UPDATED)
└── README.md            # Root documentation (UPDATED)
```

## Components and Interfaces

### 1. File System Reorganization

**Component**: Directory Migration Service

**Responsibilities**:

- Move all backend-related directories into `backend/`
- Preserve file permissions and timestamps
- Maintain git history where possible

**Directories to Move**:

- `app/` → `backend/app/`
- `tests/` → `backend/tests/`
- `storage/` → `backend/storage/`
- `logs/` → `backend/logs/`
- `config/` → `backend/config/`
- `scripts/` → `backend/scripts/`
- `docs/` → `backend/docs/`

**Files to Move**:

- `Dockerfile` → `backend/Dockerfile`
- `requirements.txt` → `backend/requirements.txt`
- `Makefile` → `backend/Makefile`
- `.env` → `backend/.env`
- `.env.example` → `backend/.env.example`
- `run.py` → `backend/run.py`
- `.dockerignore` → `backend/.dockerignore`

**Files to Keep at Root**:

- `docker-compose.yml` (orchestrates all services)
- `docker-compose.dev.yml` (development orchestration)
- `.gitignore` (repository-wide)
- `README.md` (project overview)
- `.git/` (version control)
- `.kiro/` (Kiro specs)
- `.vscode/` (editor config)
- `venv/` (virtual environment - will be recreated)

### 2. Docker Configuration Updates

**Component**: Docker Build System

**Dockerfile Changes**:

```dockerfile
# Update WORKDIR to reflect backend context
WORKDIR /app

# Copy from backend directory context
COPY requirements.txt .
COPY app/ ./app/
# ... etc
```

**docker-compose.yml Changes**:

```yaml
services:
  app:
    build:
      context: ./backend # NEW: Build from backend directory
      dockerfile: Dockerfile
    volumes:
      - ./backend/app:/app/app
      - ./backend/storage:/app/storage
      - ./backend/logs:/app/logs
    # ... rest of config
```

**Build Context**: The Docker build context will be `./backend` instead of `.`

### 3. Path Reference Updates

**Component**: Configuration Management

**Python Import Paths**:

- No changes needed (imports are relative within the app)
- Example: `from app.core.config import settings` remains unchanged

**File System Paths**:

- Storage paths: Already use relative paths (`./storage`)
- Log paths: Already use relative paths (`./logs`)
- Config paths: Already use relative paths (`./config`)

**Environment Variables**:

- `STORAGE_PATH=./storage` (relative to backend/)
- `VECTOR_DB_PATH=./storage/vector_db` (relative to backend/)
- No absolute paths to update

### 4. Makefile Updates

**Component**: Build Automation

**Strategy**: Update all Docker commands to reference the backend directory

**Example Updates**:

```makefile
# Before
build:
    docker-compose build

# After (if needed)
build:
    docker-compose build

# Volume mounts are handled by docker-compose.yml
```

**Commands to Verify**:

- `make init` - Initialize system
- `make up` - Start services
- `make down` - Stop services
- `make test` - Run tests
- `make logs` - View logs
- `make shell` - Access container shell

### 5. Documentation Updates

**Component**: Documentation System

**Root README.md**:

- Add monorepo structure explanation
- Update quick start instructions
- Add links to backend-specific README
- Prepare for future frontend documentation

**Backend README.md**:

- Create backend-specific documentation
- Include backend setup instructions
- Document backend-only development
- Reference API documentation

**Path References**:

- Update all file path examples
- Update directory structure diagrams
- Update Docker command examples

## Data Models

No data model changes required. All MongoDB schemas, Pydantic models, and database structures remain unchanged.

## Error Handling

### Migration Errors

**Scenario**: File move operations fail

- **Handling**: Use git mv to preserve history
- **Fallback**: Manual copy with verification
- **Validation**: Compare file checksums

**Scenario**: Docker build fails after reorganization

- **Handling**: Verify Dockerfile paths
- **Validation**: Test build in isolation
- **Rollback**: Git revert if needed

**Scenario**: Application fails to start

- **Handling**: Check volume mounts in docker-compose.yml
- **Validation**: Verify storage/logs directories exist
- **Fix**: Create missing directories

### Runtime Errors

**Scenario**: Storage paths not found

- **Handling**: Ensure relative paths in .env
- **Validation**: Check STORAGE_PATH environment variable
- **Fix**: Update paths to be relative to backend/

**Scenario**: Import errors in Python

- **Handling**: Verify PYTHONPATH if needed
- **Validation**: Run tests to verify imports
- **Fix**: Update sys.path if necessary (should not be needed)

## Testing Strategy

### Pre-Migration Testing

1. Run full test suite to establish baseline
2. Document all passing tests
3. Verify Docker build and startup
4. Test all Makefile commands

### Post-Migration Testing

1. Verify Docker build succeeds
2. Verify Docker containers start successfully
3. Run full test suite (should match baseline)
4. Test all API endpoints
5. Verify storage persistence
6. Verify log file creation
7. Test all Makefile commands

### Validation Checklist

- [ ] All tests pass
- [ ] API responds at http://localhost:8000
- [ ] Health check returns 200
- [ ] Swagger docs accessible at /docs
- [ ] MongoDB connection successful
- [ ] Redis connection successful
- [ ] Face recognition models load
- [ ] FAISS index loads/creates
- [ ] File uploads work
- [ ] Logs are written
- [ ] Storage directories accessible

## Migration Steps

### Phase 1: Preparation

1. Commit all current changes
2. Create backup branch
3. Run full test suite
4. Document current working state

### Phase 2: Directory Creation

1. Create `backend/` directory
2. Move directories using git mv
3. Move files using git mv
4. Verify git history preserved

### Phase 3: Configuration Updates

1. Update Dockerfile
2. Update docker-compose.yml
3. Update docker-compose.dev.yml
4. Update .gitignore if needed

### Phase 4: Documentation Updates

1. Create backend/README.md
2. Update root README.md
3. Update path references in docs
4. Update API documentation links

### Phase 5: Testing & Validation

1. Build Docker images
2. Start Docker containers
3. Run test suite
4. Test API endpoints
5. Verify all functionality

### Phase 6: Cleanup

1. Remove old venv (will be recreated)
2. Update .gitignore for new structure
3. Commit all changes
4. Tag release if needed

## Performance Considerations

- **No performance impact expected**: All code remains the same
- **Docker build time**: May increase slightly due to context path
- **Volume mounts**: Same performance (just different paths)
- **Import performance**: No change (relative imports unchanged)

## Security Considerations

- **Environment files**: Ensure .env is in backend/.gitignore
- **Secrets**: No changes to secret management
- **File permissions**: Preserve during migration
- **Docker security**: No changes to container security

## Future Considerations

### Frontend Integration

- Frontend will be added as `frontend/` directory
- Shared docker-compose.yml will orchestrate both
- Backend API will serve frontend static files in production
- Development: Frontend dev server + Backend API

### Shared Resources

- Consider `shared/` directory for common types/interfaces
- API contracts could be shared between frontend/backend
- Documentation could reference both services

### CI/CD Updates

- Build pipelines will need to reference backend/
- Test commands will need to cd into backend/
- Deployment scripts will need path updates
