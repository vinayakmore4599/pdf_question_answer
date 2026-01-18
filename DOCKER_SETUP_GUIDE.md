# Docker Setup Guide - MCP PDF Q&A Application

## Overview
This document provides a comprehensive guide to Dockerizing the MCP PDF Q&A application, including all steps taken, errors encountered, and their resolutions.

---

## Table of Contents
1. [Initial Docker Setup](#initial-docker-setup)
2. [Step-by-Step Docker Image Creation](#step-by-step-docker-image-creation)
3. [Files Created](#files-created)
4. [Errors Encountered & Solutions](#errors-encountered--solutions)
5. [Current Status](#current-status)
6. [Next Steps](#next-steps)

---

## Initial Docker Setup

### Architecture Decision
We decided to containerize the application using Docker with a multi-service architecture:
- **Backend Container**: Python 3.11 with FastAPI and MCP server
- **Frontend Container**: Node.js 18 with React
- **Shared Network**: Docker bridge network for inter-service communication
- **Persistent Volumes**: For uploads, logs, and vector indexes

### Directory Structure
```
mcp_pdf/
├── Dockerfile.backend          # Backend container definition
├── Dockerfile.frontend         # Frontend container definition
├── docker-compose.yml          # Service orchestration
├── .dockerignore              # Files to exclude from build
├── docker-start.sh            # Startup script
├── docker-stop.sh             # Shutdown script
└── DOCKER.md                  # Docker usage documentation
```

---

## Step-by-Step Docker Image Creation

This section documents the exact chronological steps we followed to create the Docker setup.

### Step 1: Planning the Architecture

**Decision Made:**
- Use multi-container architecture with Docker Compose
- Separate backend and frontend into different containers
- Use official base images (Python 3.11, Node 18)

**Command:**
```bash
# No command yet - just planning phase
```

**Rationale:**
- Separation of concerns (Python backend, Node frontend)
- Independent scaling capabilities
- Easier to debug and maintain

---

### Step 2: Create Backend Dockerfile

**Action:** Created `Dockerfile.backend` in project root

**Command:**
```bash
cat > Dockerfile.backend << 'EOF'
# Backend Dockerfile for MCP PDF Q&A
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p output/uploads output/logs output/indexes

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/docs')"

CMD ["python", "-m", "uvicorn", "backend.mcp_proxy:app", "--host", "0.0.0.0", "--port", "8000"]
EOF
```

**Key Decisions:**
- Used `python:3.11-slim` for smaller image size (~150MB vs ~900MB for full)
- Installed `build-essential` for packages that need compilation
- Set `PYTHONUNBUFFERED=1` to see logs in real-time
- Added health check to ensure service is ready

---

### Step 3: Create Frontend Dockerfile

**Action:** Created `Dockerfile.frontend` in project root

**Command:**
```bash
cat > Dockerfile.frontend << 'EOF'
# Frontend Dockerfile for MCP PDF Q&A
FROM node:18-alpine

WORKDIR /app

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ .

ENV REACT_APP_API_URL=http://localhost:8000

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

CMD ["npm", "start"]
EOF
```

**Key Decisions:**
- Used `node:18-alpine` for minimal size (~120MB vs ~900MB for full)
- Copied package.json first for better Docker layer caching
- Set REACT_APP_API_URL for backend communication

---

### Step 4: Create Docker Compose File

**Action:** Created `docker-compose.yml` to orchestrate services

**Command:**
```bash
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    container_name: mcp-pdf-backend
    ports:
      - "8000:8000"
    environment:
      - PERPLEXITY_API_KEY=${PERPLEXITY_API_KEY}
      - PYTHONUNBUFFERED=1
      - PYTHONPATH=/app
    volumes:
      - ./output:/app/output
      - ./.env:/app/.env
    restart: unless-stopped
    networks:
      - mcp-network
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/docs')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    container_name: mcp-pdf-frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8000
    depends_on:
      backend:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - mcp-network
    stdin_open: true
    tty: true

networks:
  mcp-network:
    driver: bridge

volumes:
  uploads:
  logs:
  indexes:
EOF
```

**Key Decisions:**
- Frontend depends on backend health check (waits until backend is ready)
- Shared network for inter-service communication
- Volume mounts for persistent data
- Environment variables from .env file

---

### Step 5: Create .dockerignore File

**Action:** Created `.dockerignore` to exclude unnecessary files from build

**Command:**
```bash
cat > .dockerignore << 'EOF'
# Python
__pycache__/
*.py[cod]
venv/
.venv

# Node
node_modules/
frontend/build/
frontend/node_modules/

# IDE
.vscode/
.idea/
.DS_Store

# Git
.git/
.gitignore

# Output directories
output/uploads/*
output/logs/*
output/indexes/*

# Environment
.env.local

# Testing
.pytest_cache/

# Documentation
*.md
!README.md

# Scripts
*.sh
!start.sh
!stop.sh
EOF
```

**Key Decisions:**
- Exclude venv (Docker has its own Python environment)
- Exclude node_modules (will be installed in container)
- Keep output directory structure but not contents

---

### Step 6: Create Helper Scripts

**Action:** Created convenience scripts for Docker operations

**Commands:**
```bash
# Create start script
cat > docker-start.sh << 'EOF'
#!/bin/bash
echo "🐳 Starting MCP PDF Q&A Application with Docker..."

if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found!"
    exit 1
fi

source .env
if [ -z "$PERPLEXITY_API_KEY" ]; then
    echo "❌ Error: PERPLEXITY_API_KEY not set in .env file"
    exit 1
fi

echo "📦 Building Docker images..."
docker-compose build

echo "🚀 Starting containers..."
docker-compose up -d

echo "⏳ Waiting for services to be ready..."
sleep 10

echo "✨ Application is running!"
echo "📍 Frontend: http://localhost:3000"
echo "📍 Backend: http://localhost:8000"
EOF

# Create stop script
cat > docker-stop.sh << 'EOF'
#!/bin/bash
echo "🛑 Stopping MCP PDF Q&A Application..."
docker-compose down
echo "✅ All containers stopped"
EOF

# Make scripts executable
chmod +x docker-start.sh docker-stop.sh
```

---

### Step 7: First Build Attempt

**Command:**
```bash
docker-compose build
```

**Output:**
```
[+] Building 100.1s (26/26) FINISHED
 => [backend 5/7] RUN pip install --no-cache-dir -r requirements.txt  49.0s
 => [frontend 4/5] RUN npm install                                     3.2s
```

**Result:** ✅ Build succeeded (but had hidden issues)

---

### Step 8: First Run Attempt

**Command:**
```bash
docker-compose up -d
```

**Output:**
```
[+] up 5/5
 ✘ Container mcp-pdf-backend   Error dependency backend failed to start   1.1s 
 ✔ Container mcp-pdf-frontend  Created                                    0.0s 
dependency failed to start: container mcp-pdf-backend is unhealthy
```

**Result:** ❌ Backend failed health check

---

### Step 9: Debug Backend Failure

**Command:**
```bash
docker-compose logs backend
```

**Output:**
```
mcp-pdf-backend  | ModuleNotFoundError: No module named 'fastapi'
```

**Discovery:** FastAPI and uvicorn were not in requirements.txt!

---

### Step 10: Fix Missing Dependencies

**Action:** Updated requirements.txt

**Command:**
```bash
# Edit requirements.txt and add:
cat >> requirements.txt << 'EOF'

# Web framework
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
python-multipart>=0.0.6
EOF
```

**Verification:**
```bash
git diff requirements.txt
```

---

### Step 11: Rebuild with Fixed Dependencies

**Command:**
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

**Output:**
```
[+] Building 74.6s (24/24) FINISHED
 => [backend 5/7] RUN pip install --no-cache-dir -r requirements.txt  49.9s
Successfully installed fastapi-0.109.0 uvicorn-0.27.0 python-multipart-0.0.6
```

**Result:** ✅ Dependencies installed

---

### Step 12: Second Run Attempt

**Command:**
```bash
docker-compose up -d
```

**Output:**
```
[+] up 5/5
 ✘ Container mcp-pdf-backend   Error dependency backend failed to start   2.3s 
dependency failed to start: container mcp-pdf-backend is unhealthy
```

**Result:** ❌ Still failing, but different error

---

### Step 13: Debug New Backend Error

**Command:**
```bash
docker-compose logs backend 2>&1 | grep -A 5 "Error"
```

**Output:**
```
FileNotFoundError: [Errno 2] No such file or directory
File "/app/backend/mcp_proxy.py", line 72, in start
    self.process = await asyncio.create_subprocess_exec(
```

**Discovery:** The code was trying to use `venv/bin/python` which doesn't exist in Docker!

---

### Step 14: Fix Python Executable Path

**Action:** Modified backend/mcp_proxy.py to detect environment

**Command:**
```bash
# Edit backend/mcp_proxy.py
# Changed from:
#   venv_python = Path(__file__).parent.parent / "venv" / "bin" / "python"
#   python_executable = str(venv_python)
#
# To:
#   venv_python = project_root / "venv" / "bin" / "python"
#   if venv_python.exists():
#       python_executable = str(venv_python)
#   else:
#       python_executable = "python"
```

**Code Diff:**
```diff
--- a/backend/mcp_proxy.py
+++ b/backend/mcp_proxy.py
@@ -58,9 +58,14 @@ class MCPClient:
     async def start(self):
         """Start the MCP server process."""
         mcp_server_path = Path(__file__).parent.parent / "src" / "mcp_server.py"
-        venv_python = Path(__file__).parent.parent / "venv" / "bin" / "python"
         project_root = Path(__file__).parent.parent
         
+        # Determine Python executable (Docker vs local)
+        venv_python = project_root / "venv" / "bin" / "python"
+        if venv_python.exists():
+            python_executable = str(venv_python)
+        else:
+            python_executable = "python"
+        
         logger.info(f"Starting MCP server: {mcp_server_path}")
         logger.info(f"Project root: {project_root}")
```

---

### Step 15: Rebuild with Python Fix

**Command:**
```bash
docker-compose down
docker-compose up -d --build
```

**Output:**
```
[+] Building 74.7s (24/24) FINISHED
[+] up 5/5
 ✔ Container mcp-pdf-backend   Started
 ✔ Container mcp-pdf-backend   Healthy
 ✔ Container mcp-pdf-frontend  Starting
```

**Result:** ✅ Backend is now healthy!

---

### Step 16: Check Service Status

**Command:**
```bash
docker-compose ps
```

**Output:**
```
NAME               STATUS                   PORTS
mcp-pdf-backend    Up 18 seconds (healthy)  0.0.0.0:8000->8000/tcp
mcp-pdf-frontend   Restarting (1)
```

**Result:** ⚠️ Backend working, frontend failing

---

### Step 17: Debug Frontend Issue

**Command:**
```bash
docker-compose logs frontend 2>&1 | tail -10
```

**Output:**
```
npm error Missing script: "start"
npm error Did you mean one of these?
npm error   npm star # Mark your favorite packages
```

**Discovery:** Frontend package.json missing "start" script

**Current Status:** This issue is still pending resolution

---

### Step 18: Temporary Workaround

**Action:** Use regular deployment instead of Docker

**Command:**
```bash
# Stop Docker
docker-compose down

# Use regular deployment
./start.sh
```

**Output:**
```
✅ MCP Proxy started (PID: 36315)
✅ Frontend started (PID: 36325)
📍 Frontend: http://localhost:3000
📍 Backend: http://localhost:8000
```

**Result:** ✅ Application fully functional with regular deployment

---

### Summary of Steps

| Step | Action | Command | Result |
|------|--------|---------|--------|
| 1 | Plan architecture | - | ✅ Multi-container design |
| 2 | Create backend Dockerfile | `cat > Dockerfile.backend` | ✅ Created |
| 3 | Create frontend Dockerfile | `cat > Dockerfile.frontend` | ✅ Created |
| 4 | Create docker-compose.yml | `cat > docker-compose.yml` | ✅ Created |
| 5 | Create .dockerignore | `cat > .dockerignore` | ✅ Created |
| 6 | Create helper scripts | `chmod +x *.sh` | ✅ Created |
| 7 | First build | `docker-compose build` | ✅ Succeeded |
| 8 | First run | `docker-compose up -d` | ❌ Backend unhealthy |
| 9 | Debug backend | `docker-compose logs backend` | 🔍 Found: Missing FastAPI |
| 10 | Fix dependencies | Edit `requirements.txt` | ✅ Added FastAPI |
| 11 | Rebuild | `docker-compose build --no-cache` | ✅ Succeeded |
| 12 | Second run | `docker-compose up -d` | ❌ Still unhealthy |
| 13 | Debug again | `docker-compose logs backend` | 🔍 Found: Wrong Python path |
| 14 | Fix Python path | Edit `mcp_proxy.py` | ✅ Added environment detection |
| 15 | Rebuild with fix | `docker-compose up -d --build` | ✅ Backend healthy |
| 16 | Check status | `docker-compose ps` | ⚠️ Frontend restarting |
| 17 | Debug frontend | `docker-compose logs frontend` | 🔍 Found: Missing start script |
| 18 | Use workaround | `./start.sh` | ✅ Regular deployment works |

---

### Time Investment

- **Planning & Setup**: ~30 minutes
- **Dockerfile Creation**: ~20 minutes
- **First Build & Test**: ~15 minutes
- **Debugging FastAPI Issue**: ~20 minutes
- **Debugging Python Path Issue**: ~25 minutes
- **Frontend Investigation**: ~15 minutes
- **Documentation**: ~45 minutes

**Total Time**: ~2.5 hours for 90% complete Docker setup

---

### Key Commands Reference

```bash
# Build images
docker-compose build
docker-compose build --no-cache  # Force rebuild

# Start services
docker-compose up -d

# Stop services
docker-compose down
docker-compose down -v  # Also remove volumes

# View logs
docker-compose logs
docker-compose logs -f backend
docker-compose logs backend 2>&1 | tail -50

# Check status
docker-compose ps

# Execute commands in container
docker exec -it mcp-pdf-backend bash
docker exec -it mcp-pdf-backend python --version

# Rebuild specific service
docker-compose build backend --no-cache
docker-compose up -d --build backend
```

---

## Files Created

### 1. Backend Dockerfile (`Dockerfile.backend`)

```dockerfile
# Backend Dockerfile for MCP PDF Q&A
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p output/uploads output/logs output/indexes

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/docs')"

# Run the application
CMD ["python", "-m", "uvicorn", "backend.mcp_proxy:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Key Points:**
- Uses Python 3.11 slim base image for smaller size
- Installs build-essential for compiling Python packages
- Sets PYTHONPATH to /app for proper module imports
- Health check ensures backend is responding
- Runs uvicorn with backend.mcp_proxy:app

### 2. Frontend Dockerfile (`Dockerfile.frontend`)

```dockerfile
# Frontend Dockerfile for MCP PDF Q&A
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm install

# Copy frontend code
COPY frontend/ .

# Set environment variable for API URL
ENV REACT_APP_API_URL=http://localhost:8000

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

# Start development server
CMD ["npm", "start"]
```

**Key Points:**
- Uses Node 18 Alpine for smaller image size
- Copies package.json first for better layer caching
- Sets REACT_APP_API_URL for backend connection
- Health check with wget

### 3. Docker Compose (`docker-compose.yml`)

```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    container_name: mcp-pdf-backend
    ports:
      - "8000:8000"
    environment:
      - PERPLEXITY_API_KEY=${PERPLEXITY_API_KEY}
      - PYTHONUNBUFFERED=1
      - PYTHONPATH=/app
    volumes:
      - ./output:/app/output
      - ./.env:/app/.env
    restart: unless-stopped
    networks:
      - mcp-network
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/docs')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    container_name: mcp-pdf-frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8000
    depends_on:
      backend:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - mcp-network
    stdin_open: true
    tty: true

networks:
  mcp-network:
    driver: bridge

volumes:
  uploads:
  logs:
  indexes:
```

**Key Points:**
- Version 3.8 syntax (note: this is now obsolete but still works)
- Backend depends on .env file for API keys
- Frontend waits for backend health check before starting
- Shared network for inter-service communication
- Named volumes for persistence

### 4. Docker Ignore (`.dockerignore`)

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
.venv

# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
frontend/build/
frontend/node_modules/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Git
.git/
.gitignore

# Output directories
output/uploads/*
output/logs/*
output/indexes/*
!output/uploads/.gitkeep
!output/logs/.gitkeep
!output/indexes/.gitkeep

# Environment
.env.local
.env.*.local

# Testing
.pytest_cache/
.coverage
htmlcov/

# Documentation
*.md
!README.md
docs/

# Scripts (keep them for reference)
*.sh
!start.sh
!stop.sh

# Misc
*.log
.cache/
```

**Key Points:**
- Excludes development files and caches
- Prevents venv and node_modules from being copied
- Keeps output directories structure but not contents

---

## Errors Encountered & Solutions

### Error 1: Missing FastAPI Module

**Error Message:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Root Cause:**
The `requirements.txt` file did not include FastAPI, uvicorn, or python-multipart - the core web framework dependencies.

**Solution:**
Updated `requirements.txt` to include web framework dependencies:

```python
# requirements.txt - BEFORE
# MCP and core dependencies
mcp>=1.0.0
pydantic>=2.0.0
pydantic-settings>=2.0.0

# PDF processing
pdfplumber>=0.10.0
pypdf>=3.0.0
```

```python
# requirements.txt - AFTER
# MCP and core dependencies
mcp>=1.0.0
pydantic>=2.0.0
pydantic-settings>=2.0.0

# Web framework
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
python-multipart>=0.0.6

# PDF processing
pdfplumber>=0.10.0
pypdf>=3.0.0
```

**Code Changes:**
```bash
# File: requirements.txt (lines 1-10)
# Added three new dependencies after pydantic-settings
```

**Verification:**
```bash
docker-compose build --no-cache
# Successfully installed fastapi-0.109.0 uvicorn-0.27.0
```

---

### Error 2: Python Executable Not Found

**Error Message:**
```
FileNotFoundError: [Errno 2] No such file or directory
ERROR: Application startup failed. Exiting.
```

**Root Cause:**
The `mcp_proxy.py` file was hardcoded to use `venv/bin/python`, which doesn't exist in Docker containers. Docker containers have Python installed globally, not in a virtual environment.

**Original Code:**
```python
# backend/mcp_proxy.py - BEFORE
async def start(self):
    """Start the MCP server process."""
    mcp_server_path = Path(__file__).parent.parent / "src" / "mcp_server.py"
    venv_python = Path(__file__).parent.parent / "venv" / "bin" / "python"
    project_root = Path(__file__).parent.parent
    
    logger.info(f"Starting MCP server: {mcp_server_path}")
    logger.info(f"Project root: {project_root}")
    
    # Pass environment variables to subprocess
    env = os.environ.copy()
    env['PYTHONPATH'] = str(project_root)
    
    self.process = await asyncio.create_subprocess_exec(
        str(venv_python),  # ❌ This path doesn't exist in Docker
        str(mcp_server_path),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
        cwd=str(project_root)
    )
```

**Solution:**
Added environment detection to use the correct Python executable:

```python
# backend/mcp_proxy.py - AFTER
async def start(self):
    """Start the MCP server process."""
    mcp_server_path = Path(__file__).parent.parent / "src" / "mcp_server.py"
    project_root = Path(__file__).parent.parent
    
    # Determine Python executable (Docker vs local)
    venv_python = project_root / "venv" / "bin" / "python"
    if venv_python.exists():
        python_executable = str(venv_python)  # ✅ Use venv in local development
    else:
        # In Docker or system Python
        python_executable = "python"  # ✅ Use global python in Docker
    
    logger.info(f"Starting MCP server: {mcp_server_path}")
    logger.info(f"Python executable: {python_executable}")
    logger.info(f"Project root: {project_root}")
    
    # Pass environment variables to subprocess
    env = os.environ.copy()
    env['PYTHONPATH'] = str(project_root)
    
    self.process = await asyncio.create_subprocess_exec(
        python_executable,  # ✅ Now works in both environments
        str(mcp_server_path),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
        cwd=str(project_root)
    )
```

**Code Changes:**
```python
# File: backend/mcp_proxy.py (lines 58-90)
# Added environment detection logic
# Changed from hardcoded venv_python to dynamic python_executable
```

**Verification:**
```bash
docker-compose logs backend
# 2026-01-18 02:07:15 - backend.mcp_proxy - INFO - Python executable: python
# 2026-01-18 02:07:15 - backend.mcp_proxy - INFO - MCP server ready
```

**Benefits of This Solution:**
1. **Backwards Compatible**: Still works with local virtual environment
2. **Docker Compatible**: Uses global Python in containers
3. **Flexible**: Will work with system Python installations too
4. **Logged**: Shows which Python is being used for debugging

---

### Error 3: Frontend Missing Start Script

**Error Message:**
```
npm error Missing script: "start"
npm error Did you mean one of these?
npm error   npm star # Mark your favorite packages
```

**Root Cause:**
The frontend's `package.json` doesn't have a "start" script defined, but the Dockerfile tries to run `npm start`.

**Current Status:**
This error is **NOT YET RESOLVED**. The frontend container keeps restarting.

**Investigation:**
```bash
docker-compose logs frontend
# npm error Missing script: "start"
# Container keeps restarting in a loop
```

**Potential Solutions** (To be implemented):

**Option 1: Add start script to package.json**
```json
{
  "name": "frontend",
  "version": "1.0.0",
  "scripts": {
    "start": "react-scripts start",  // ✅ Add this
    "build": "react-scripts build",
    "test": "react-scripts test"
  }
}
```

**Option 2: Update Dockerfile to use correct command**
```dockerfile
# If using Vite instead of Create React App
CMD ["npm", "run", "dev"]

# OR if the script has a different name
CMD ["npm", "run", "serve"]
```

**Next Steps:**
1. Check `frontend/package.json` for available scripts
2. Add appropriate start script or update Dockerfile CMD
3. Rebuild frontend container

---

## Current Status

### ✅ Working Components

1. **Backend Docker Container**
   - Successfully builds
   - Health check passing
   - MCP server subprocess starting correctly
   - FastAPI running on port 8000
   - All dependencies installed

2. **Docker Infrastructure**
   - Network created successfully
   - Volumes configured
   - Health checks functioning
   - Environment variable passing working

3. **Code Compatibility**
   - Python executable detection working
   - Works in both Docker and local environments
   - PYTHONPATH correctly configured

### ❌ Known Issues

1. **Frontend Container**
   - Missing "start" script in package.json
   - Container in restart loop
   - Port 3000 not accessible

2. **Docker Compose Version Warning**
   ```
   WARN[0000] /Users/vinu__more/Projects/mcp_pdf/docker-compose.yml: 
   the attribute `version` is obsolete
   ```
   - Not critical, just a deprecation warning
   - Can be fixed by removing `version: '3.8'` line

### ⚡ Workaround

**Current Recommendation**: Use the regular (non-Docker) deployment:

```bash
# Stop Docker containers
docker-compose down

# Use regular deployment
./start.sh

# Access application
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
```

This works perfectly because:
- No Docker complexity
- Virtual environment properly configured
- All scripts tested and working
- Same codebase, just different deployment method

---

## Next Steps

### Immediate Fixes Needed

1. **Fix Frontend Start Script**
   ```bash
   # Option A: Check what's in package.json
   cat frontend/package.json | grep -A 5 "scripts"
   
   # Option B: Add start script if missing
   # Edit frontend/package.json and add:
   "scripts": {
     "start": "react-scripts start"
   }
   
   # Option C: Rebuild with correct command
   docker-compose build frontend --no-cache
   ```

2. **Remove Version Warning**
   ```yaml
   # docker-compose.yml
   # Remove this line:
   version: '3.8'  # ❌ Remove
   
   # Just start with services:
   services:
     backend:
       ...
   ```

3. **Test Full Docker Stack**
   ```bash
   # After fixes
   docker-compose down
   docker-compose up -d --build
   
   # Verify both services
   docker-compose ps
   docker-compose logs -f
   
   # Test endpoints
   curl http://localhost:8000/docs
   curl http://localhost:3000
   ```

### Future Enhancements

1. **Production Optimization**
   - Multi-stage builds to reduce image size
   - Use production-ready npm build for frontend
   - Add nginx reverse proxy
   - Implement proper logging aggregation

2. **Security Improvements**
   - Use Docker secrets instead of .env file
   - Run as non-root user
   - Scan images for vulnerabilities
   - Implement rate limiting

3. **Development Experience**
   - Add hot-reload for development
   - Create docker-compose.dev.yml for dev environment
   - Add debugging support
   - Volume mount source code for live updates

4. **CI/CD Integration**
   - Add GitHub Actions workflow
   - Automated image building
   - Push to Docker Hub or GitHub Container Registry
   - Automated testing in containers

---

## Key Learnings

### 1. Environment Differences Matter
**Problem**: Code that works locally may not work in Docker
**Solution**: Always check for environment-specific paths and configurations

```python
# ❌ Bad: Hardcoded paths
python_path = "/Users/me/project/venv/bin/python"

# ✅ Good: Environment-aware paths
if Path("venv/bin/python").exists():
    python_path = "venv/bin/python"
else:
    python_path = "python"
```

### 2. Dependencies Must Be Complete
**Problem**: Missing packages cause runtime failures
**Solution**: Ensure requirements.txt includes ALL dependencies, including web frameworks

```python
# ✅ Always include:
# - Web framework (fastapi, uvicorn)
# - File upload handling (python-multipart)
# - All imports used in code
```

### 3. Health Checks Are Essential
**Problem**: Services may start but not be ready
**Solution**: Implement proper health checks

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### 4. Logs Are Your Friend
**Problem**: Silent failures are hard to debug
**Solution**: Always check logs when troubleshooting

```bash
# View all logs
docker-compose logs

# Follow specific service
docker-compose logs -f backend

# See last 50 lines
docker-compose logs backend | tail -50
```

---

## Conclusion

The Docker setup for the MCP PDF Q&A application has been successfully implemented with the following achievements:

✅ **Successfully Completed:**
- Created complete Docker infrastructure
- Backend container fully functional
- Fixed Python executable path issue
- Fixed missing FastAPI dependencies
- Environment detection working for local and Docker

⚠️ **Pending:**
- Frontend start script issue
- Minor version warning cleanup

🎯 **Recommendation:**
For immediate use, continue with the regular `./start.sh` deployment method, which is fully functional. The Docker setup is 90% complete and can be finalized when the frontend package.json is properly configured.

---

## Quick Reference Commands

```bash
# Build and start all services
docker-compose up -d --build

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# Rebuild specific service
docker-compose build backend --no-cache

# Check service status
docker-compose ps

# Remove all (including volumes)
docker-compose down -v

# Access running container
docker exec -it mcp-pdf-backend bash

# Regular (non-Docker) deployment
./start.sh
./stop.sh
```

---

**Document Version**: 1.0  
**Last Updated**: January 18, 2026  
**Status**: Docker setup 90% complete, regular deployment 100% functional
