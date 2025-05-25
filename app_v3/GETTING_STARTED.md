# Getting Started Guide

> 🚀 Quick setup guide for the Voice-Cloned Talking-Head Lecturer application

## Prerequisites

Before starting, ensure you have:
- **Docker & Docker Compose** (for services)
- **Python 3.9+** (for backend development)
- **Git** (for version control)
- **PostgreSQL client** (optional, for database inspection)

## 🏁 Quick Start (5 minutes)

### 1. Clone and Setup Environment

```bash
git clone <repository-url>
cd digitalclone-iitg/app_v3

# Copy environment template
cp .env.example .env

# Edit .env file with your settings (optional for development)
# nano .env
```

### 2. Start Supporting Services

```bash
# Start PostgreSQL, Redis, MinIO, and other services
docker-compose up -d

# Verify services are running
docker-compose ps
```

**Expected services:**
- `postgresql` - Database (port 5432)
- `redis` - Cache/Queue (port 6379)  
- `minio` - File storage (port 9000)
- `minio-client` - MinIO setup

### 3. Initialize Database

```bash
# Install Python dependencies
cd backend
pip install -r requirements.txt
cd ..

# Initialize database with default admin user
python scripts/init_db.py init
```

**Output should show:**
```
✅ Database tables created successfully!
✅ Default admin user created!
📧 Email: admin@voiceclone.edu
🔑 Password: AdminPass123
```

### 4. Start Development Server

```bash
# Start the Flask API server
python scripts/run_dev.py
```

**Server will start on:** http://localhost:5000

### 5. Test Authentication System

```bash
# In a new terminal, run authentication tests
python scripts/test_auth.py
```

**Expected output:**
```
🚀 Starting authentication tests...
✅ Health check passed!
✅ Registration successful!
✅ Login successful!
✅ Profile retrieved!
...
🎉 All tests completed!
```

## 🔧 Development Commands

### Database Management

```bash
# Initialize database (first time)
python scripts/init_db.py init

# Reset database (WARNING: deletes all data)
python scripts/init_db.py reset

# Check database status
python scripts/init_db.py check
```

### Server Management

```bash
# Start development server
python scripts/run_dev.py

# Start with custom host/port
FLASK_HOST=0.0.0.0 FLASK_PORT=8000 python scripts/run_dev.py

# Start with debug disabled
FLASK_DEBUG=false python scripts/run_dev.py
```

### Testing

```bash
# Test authentication endpoints
python scripts/test_auth.py

# Test with custom server URL
python scripts/test_auth.py http://localhost:8000

# Run backend tests (when available)
cd backend && pytest
```

### Docker Services

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Reset volumes (WARNING: deletes all data)
docker-compose down -v
```

## 📋 Available Endpoints

Once the server is running, these endpoints are available:

### Health & Status
- `GET /health` - Server health check

### Authentication (✅ COMPLETED)
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Refresh access token
- `POST /api/auth/logout` - User logout
- `GET /api/auth/profile` - Get user profile
- `PUT /api/auth/profile` - Update user profile
- `POST /api/auth/change-password` - Change password
- `POST /api/auth/verify-token` - Verify token validity

### Assets (🚧 IN PROGRESS)
- `POST /api/assets/upload` - Upload portrait/voice files
- `GET /api/assets` - List user assets
- `DELETE /api/assets/{id}` - Delete asset

### Jobs (⏳ COMING SOON)
- `GET /api/jobs` - List user jobs
- `POST /api/jobs` - Create new job
- `GET /api/jobs/{id}` - Get job status

### Generation (⏳ COMING SOON)
- `POST /api/generate/script` - Generate script with LLM
- `POST /api/generate/voice-clone` - Clone voice
- `POST /api/generate/text-to-speech` - Convert text to speech
- `POST /api/generate/video` - Generate talking-head video
- `POST /api/generate/full-pipeline` - Run complete pipeline

## 🎯 Test Data

### Default Admin Account
- **Email**: `admin@voiceclone.edu`
- **Password**: `AdminPass123`
- **Role**: Admin
- ⚠️ **Change password after first login!**

### Test User Registration
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "professor@university.edu",
    "username": "prof_smith",
    "password": "SecurePass123",
    "confirm_password": "SecurePass123",
    "first_name": "John",
    "last_name": "Smith",
    "department": "Computer Science",
    "title": "Professor",
    "role": "faculty"
  }'
```

## 🔍 Service URLs

When running in development mode:

- **API Server**: http://localhost:5000
- **MinIO Console**: http://localhost:9001 (admin/minioadmin)
- **Redis**: localhost:6379
- **PostgreSQL**: localhost:5432

## 🚨 Troubleshooting

### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker-compose ps postgresql

# View PostgreSQL logs
docker-compose logs postgresql

# Restart PostgreSQL
docker-compose restart postgresql
```

### Redis Connection Issues
```bash
# Check if Redis is running
docker-compose ps redis

# Test Redis connection
docker-compose exec redis redis-cli ping
```

### Permission Issues
```bash
# Make scripts executable
chmod +x scripts/*.py
```

### Port Conflicts
```bash
# Check what's using port 5000
lsof -i :5000

# Use different port
FLASK_PORT=8000 python scripts/run_dev.py
```

## 📈 Next Steps

1. **Complete Stage 2**: Asset ingest with MinIO integration
2. **Complete Stage 3**: Job management system
3. **Complete Stage 4**: Celery worker setup
4. **Complete Stage 5-6**: AI service integrations
5. **Complete Stage 7**: React frontend

## 🔒 Security Notes

- Default passwords should be changed in production
- JWT secrets should be properly configured
- Database credentials should be secured
- File upload limits are enforced
- CORS is configured for development

---

**Questions or issues?** Check the [troubleshooting section](#🚨-troubleshooting) or create an issue.
