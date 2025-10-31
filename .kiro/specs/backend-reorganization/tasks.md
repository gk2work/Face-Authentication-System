# Implementation Plan

- [x] 1. Prepare for migration
  - Create backup of current state by committing all changes
  - Run full test suite to establish baseline
  - Document current Docker setup and verify it works
  - _Requirements: 1.2, 4.1_

- [x] 2. Create backend directory structure
  - Create `backend/` directory at project root
  - Move `app/` directory to `backend/app/` using git mv
  - Move `tests/` directory to `backend/tests/` using git mv
  - Move `storage/` directory to `backend/storage/` using git mv
  - Move `logs/` directory to `backend/logs/` using git mv
  - Move `config/` directory to `backend/config/` using git mv
  - Move `scripts/` directory to `backend/scripts/` using git mv
  - Move `docs/` directory to `backend/docs/` using git mv
  - _Requirements: 1.1, 1.3_

- [x] 3. Move backend configuration files
  - Move `Dockerfile` to `backend/Dockerfile` using git mv
  - Move `requirements.txt` to `backend/requirements.txt` using git mv
  - Move `Makefile` to `backend/Makefile` using git mv
  - Move `.env` to `backend/.env` using git mv
  - Move `.env.example` to `backend/.env.example` using git mv
  - Move `run.py` to `backend/run.py` using git mv
  - Move `.dockerignore` to `backend/.dockerignore` using git mv
  - _Requirements: 1.1, 1.3_

- [x] 4. Update Docker configuration
- [x] 4.1 Update Dockerfile paths
  - Verify WORKDIR is set to /app
  - Ensure all COPY commands use correct relative paths
  - Verify no absolute path references exist
  - _Requirements: 2.1, 2.3_

- [x] 4.2 Update docker-compose.yml
  - Change build context to `./backend`
  - Update volume mounts to reference `./backend/app`, `./backend/storage`, `./backend/logs`
  - Verify environment variables are correctly passed
  - Ensure network configuration remains unchanged
  - _Requirements: 2.2, 2.4_

- [x] 4.3 Update docker-compose.dev.yml
  - Change build context to `./backend`
  - Update volume mounts to reference backend directory
  - Verify development-specific configurations
  - _Requirements: 2.2, 2.4_

- [x] 5. Update Makefile commands
  - Update any path references in Makefile to work from project root
  - Verify docker-compose commands work with new structure
  - Test that make commands execute from project root
  - Update shell command to access backend container correctly
  - _Requirements: 4.1, 4.2_

- [x] 6. Update .gitignore
  - Add `backend/.env` to gitignore
  - Add `backend/venv/` to gitignore
  - Add `backend/storage/photographs/*` to gitignore
  - Add `backend/storage/vector_db/*` to gitignore
  - Add `backend/logs/*` to gitignore
  - Remove old root-level ignore patterns that are now in backend/
  - _Requirements: 1.3_

- [x] 7. Create backend-specific README
  - Create `backend/README.md` with backend setup instructions
  - Document how to run backend in isolation
  - Include API documentation links
  - Document environment variable configuration
  - Add troubleshooting section for backend issues
  - _Requirements: 3.1, 3.2, 3.3_

- [x] 8. Update root README
  - Update project structure diagram to show backend/ directory
  - Add monorepo structure explanation
  - Update quick start instructions to reference backend/
  - Update all file path examples to include backend/ prefix
  - Add section explaining backend-only vs full-stack development
  - Document the rationale for monorepo structure
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 9. Update documentation files
  - Update all path references in `backend/docs/` files
  - Update code examples to reflect new structure
  - Update deployment guides with new paths
  - Verify all documentation links still work
  - _Requirements: 3.2_

- [x] 10. Verify and test the migration
- [x] 10.1 Test Docker build
  - Run `docker-compose build` from project root
  - Verify build completes without errors
  - Check that all dependencies are installed correctly
  - _Requirements: 2.3, 4.4_

- [x] 10.2 Test Docker startup
  - Run `docker-compose up` from project root
  - Verify all containers start successfully
  - Check that API is accessible at http://localhost:8000
  - Verify MongoDB and Redis connections work
  - _Requirements: 2.3, 4.4_

- [x] 10.3 Run test suite
  - Execute tests from within the backend container
  - Verify all tests pass (match baseline)
  - Check that test coverage remains the same
  - _Requirements: 4.2, 4.3, 5.5_

- [x] 10.4 Test API endpoints
  - Test health check endpoint (GET /health)
  - Test readiness endpoint (GET /ready)
  - Test application submission endpoint
  - Test authentication endpoints
  - Verify Swagger docs at /docs
  - _Requirements: 1.2, 5.5_

- [x] 10.5 Verify storage and logging
  - Test file upload to verify storage paths work
  - Check that logs are written to backend/logs/
  - Verify FAISS index loads from backend/storage/vector_db/
  - Test that photographs are saved to backend/storage/photographs/
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 10.6 Test Makefile commands
  - Test `make up` command
  - Test `make down` command
  - Test `make logs` command
  - Test `make shell` command
  - Test `make test` command
  - Test `make health` command
  - _Requirements: 4.1, 4.2_

- [-] 11. Clean up and finalize
  - Remove old `venv/` directory from root (will be recreated in backend/)
  - Verify no orphaned files remain at root level
  - Commit all changes with descriptive message
  - Create git tag for this reorganization milestone
  - _Requirements: 1.1, 1.3_

- [ ] 12. Update CI/CD configurations (if applicable)
  - Update build scripts to reference backend/ directory
  - Update test commands to run from backend/ context
  - Update deployment scripts with new paths
  - Verify CI/CD pipeline works with new structure
  - _Requirements: 4.3_
