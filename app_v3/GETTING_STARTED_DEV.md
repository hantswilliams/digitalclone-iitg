# Getting Started - Development Environment

This guide will help you set up and run the Voice Clone application in development mode with hot reloading and easy debugging.

## Prerequisites

- **Docker & Docker Compose** - For running Redis and MinIO services
- **Python 3.8+** - For running the Flask backend and Celery worker
- **Node.js 16+** - For running the React frontend
- **Git** - For version control

## Architecture Overview

In development mode, we run:
- **Redis & MinIO**: In Docker containers (infrastructure services)
- **Flask Backend**: Locally on port 5001 (for hot reloading)
- **Celery Worker**: Locally (for easy debugging)
- **React Frontend**: Locally on port 3000 (with hot reloading)

## Step-by-Step Setup

### 1. Start Infrastructure Services

First, start Redis and MinIO using Docker Compose:

```bash
cd app_v3
docker-compose -f docker-compose-dev.yaml up -d
```

**Verify services are running:**
```bash
# Check container status
docker-compose -f docker-compose-dev.yaml ps

# Test Redis connection
docker exec $(docker-compose -f docker-compose-dev.yaml ps -q redis) redis-cli ping

# Test MinIO (should return XML response)
curl http://localhost:9000/minio/health/live
```

**Service URLs:**
- Redis: `localhost:6379`
- MinIO API: `localhost:9000`
- MinIO Console: `localhost:9001` (login: `minioadmin/minioadmin`)

### 2. Set Up Python Backend Environment

```bash
cd backend

# Create virtual environment (if not exists)
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 3. Configure Environment Variables

Ensure your `backend/.env` file has the correct local development settings:

```bash
# Check your .env file
cat .env
```

Key settings for local development:
```env
FLASK_ENV=development
DATABASE_URL=sqlite:///voice_clone_dev.db
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
MINIO_ENDPOINT=localhost:9000
PORT=5001
```

### 4. Initialize Database (First Time Only)

```bash
cd backend

# Initialize database
python -c "from app import create_app; from app.extensions import db; app = create_app(); app.app_context().push(); db.create_all()"
```

### 5. Start Celery Worker

Open a new terminal window and start the Celery worker:

```bash
cd app_v3/backend
source venv/bin/activate  # Activate virtual environment
python run_celery.py worker --loglevel=info
```

**Expected output:**
```
[2025-05-27 10:00:00,000: INFO/MainProcess] Connected to redis://localhost:6379/0
[2025-05-27 10:00:00,000: INFO/MainProcess] mingle: searching for available nodes...
[2025-05-27 10:00:00,000: INFO/MainProcess] celery@hostname ready.
```

### 6. Start Flask Backend

Open another new terminal window and start the Flask development server:

```bash
cd app_v3/backend
source venv/bin/activate  # Activate virtual environment
PORT=5001 python app.py
```

**Expected output:**
```
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5001
 * Running on http://[::1]:5001
```

**Test the backend:**
```bash
curl http://localhost:5001/health
# Should return: {"status": "healthy"}
```

### 7. Start React Frontend

Open another new terminal window and start the React development server:

```bash
cd app_v3/frontend

# Install dependencies (first time only)
npm install

# Start development server
npm start
```

**Expected output:**
```
Compiled successfully!

You can now view frontend in the browser.

  Local:            http://localhost:3000
  On Your Network:  http://192.168.1.x:3000
```

## Development Workflow

### Daily Development Routine

1. **Start infrastructure services:**
   ```bash
   cd app_v3
   docker-compose -f docker-compose-dev.yaml up -d
   ```

2. **Start Celery worker** (Terminal 1):
   ```bash
   cd app_v3/backend && source venv/bin/activate && python run_celery.py worker --loglevel=info
   ```

3. **Start Flask backend** (Terminal 2):
   ```bash
   cd app_v3/backend && source venv/bin/activate && PORT=5001 python app.py
   ```

4. **Start React frontend** (Terminal 3):
   ```bash
   cd app_v3/frontend && npm start
   ```

### Stopping Services

**Stop application services:**
- Press `Ctrl+C` in each terminal running Flask, Celery, and React

**Stop infrastructure services:**
```bash
cd app_v3
docker-compose -f docker-compose-dev.yaml down
```

**Complete cleanup (removes data volumes):**
```bash
cd app_v3
docker-compose -f docker-compose-dev.yaml down -v
```

## Service URLs & Access

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5001
- **MinIO Console**: http://localhost:9001 (admin: `minioadmin/minioadmin`)
- **Redis**: localhost:6379 (use Redis CLI or GUI tools)

## Troubleshooting

### Common Issues

1. **Port already in use:**
   ```bash
   # Check what's using the port
   lsof -i :5001  # or :3000, :6379, :9000
   
   # Kill process if needed
   kill -9 <PID>
   ```

2. **Redis connection refused:**
   ```bash
   # Check if Redis container is running
   docker-compose -f docker-compose-dev.yaml ps
   
   # Restart Redis
   docker-compose -f docker-compose-dev.yaml restart redis
   ```

3. **MinIO access denied:**
   - Verify credentials in `.env` match MinIO container settings
   - Check MinIO console at http://localhost:9001

4. **Database issues:**
   ```bash
   # Reset database
   cd backend
   rm -f instance/voice_clone_dev.db
   python -c "from app import create_app; from app.extensions import db; app = create_app(); app.app_context().push(); db.create_all()"
   ```

5. **Python dependencies issues:**
   ```bash
   cd backend
   pip install --upgrade pip
   pip install -r requirements.txt --force-reinstall
   ```

### Checking Service Health

```bash
# Check all Docker services
docker-compose -f docker-compose-dev.yaml ps

# Test Redis
docker exec $(docker-compose -f docker-compose-dev.yaml ps -q redis) redis-cli ping

# Test MinIO
curl -f http://localhost:9000/minio/health/live

# Test Flask backend
curl http://localhost:5001/health

# Check Celery worker status
# Look for "celery@hostname ready" message in worker terminal
```

## Development Tips

1. **Code Changes**: Flask and React will auto-reload on file changes
2. **Celery Changes**: Restart Celery worker after modifying task code
3. **Database Changes**: Run database migrations when models change
4. **Environment Changes**: Restart Flask backend after `.env` changes
5. **Dependency Changes**: Restart services after adding new packages

## Next Steps

- Check the API documentation at http://localhost:5001/docs (if implemented)
- Review the main `README.md` for feature documentation
- Explore the `backend/tests/` directory for running tests
- Check `frontend/src/` for React component structure
