# Docker Deployment Guide

## Quick Start with Docker

### Prerequisites
- Docker installed ([Get Docker](https://docs.docker.com/get-docker/))
- Docker Compose installed (included with Docker Desktop)
- Perplexity API key

### Setup & Run

1. **Configure environment**:
   ```bash
   # Add your API key to .env file
   echo "PERPLEXITY_API_KEY=your_key_here" >> .env
   ```

2. **Start the application**:
   ```bash
   ./docker-start.sh
   ```

   Or manually:
   ```bash
   docker-compose up -d
   ```

3. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Management Commands

**View logs**:
```bash
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Frontend only
docker-compose logs -f frontend
```

**Stop the application**:
```bash
./docker-stop.sh
# or
docker-compose down
```

**Restart services**:
```bash
docker-compose restart

# Restart specific service
docker-compose restart backend
docker-compose restart frontend
```

**Rebuild after code changes**:
```bash
docker-compose down
docker-compose build
docker-compose up -d
```

**Remove all data (volumes)**:
```bash
docker-compose down -v
```

### Architecture

```
┌─────────────────────────────────────────────┐
│              Docker Network                  │
│                                              │
│  ┌────────────────┐    ┌─────────────────┐ │
│  │   Frontend     │    │    Backend      │ │
│  │   (React)      │───▶│  (FastAPI +     │ │
│  │   Port: 3000   │    │   MCP Server)   │ │
│  └────────────────┘    │   Port: 8000    │ │
│                        └─────────────────┘ │
│                               │             │
│                               ▼             │
│                        ┌─────────────────┐ │
│                        │  Shared Volume  │ │
│                        │  (uploads, logs)│ │
│                        └─────────────────┘ │
└─────────────────────────────────────────────┘
```

### Services

**Backend Container**:
- Python 3.11
- FastAPI server
- MCP server (subprocess)
- RAG system with embeddings
- Port: 8000

**Frontend Container**:
- Node.js 18
- React application
- Development server
- Port: 3000

### Volumes

Persistent data is stored in:
- `./output/uploads` - Uploaded PDF files
- `./output/logs` - Application logs
- `./output/indexes` - Vector store indexes

### Environment Variables

Configure in `.env` file:
```bash
PERPLEXITY_API_KEY=your_api_key_here
```

### Troubleshooting

**Backend not starting**:
```bash
docker-compose logs backend
```

**Frontend can't connect to backend**:
- Check if backend is healthy: `docker-compose ps`
- Verify port 8000 is accessible: `curl http://localhost:8000/docs`

**Port already in use**:
```bash
# Stop existing services
./stop.sh  # Stop non-Docker version
docker-compose down

# Or change ports in docker-compose.yml
```

**Rebuild after dependency changes**:
```bash
docker-compose build --no-cache
docker-compose up -d
```

### Development Workflow

For active development, you might prefer running without Docker:
```bash
# Native development
./start.sh

# Docker deployment
./docker-start.sh
```

### Production Considerations

For production deployment:

1. **Use production builds**:
   - Update Dockerfile.frontend to use `npm run build` and serve static files
   - Use production-grade WSGI server (already using uvicorn)

2. **Add reverse proxy** (nginx/traefik)

3. **Enable HTTPS**

4. **Set resource limits** in docker-compose.yml:
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2'
         memory: 4G
   ```

5. **Use secrets** instead of .env file

6. **Enable monitoring** (prometheus, grafana)
