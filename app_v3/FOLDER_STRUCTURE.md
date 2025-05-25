# App V3 - Folder Structure

This document outlines the complete folder structure for the Voice-Cloned Talking-Head Lecturer application.

## 📁 Project Structure

```
app_v3/
├── 📋 Architecture Documents
│   ├── arch.md                           # High-level architecture diagram
│   ├── core_components.md                # Technology stack overview
│   ├── voice_clone_talking_head_outline.txt  # Complete project outline
│   └── voice_clone_workflow.md           # Generation workflow details
│
├── 🐍 Backend (Flask + Celery)
│   ├── app/
│   │   ├── __init__.py                   # Flask app factory
│   │   ├── config.py                     # Configuration settings
│   │   ├── extensions.py                 # Flask extensions (SQLAlchemy, JWT, etc.)
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                   # Authentication endpoints
│   │   │   ├── assets.py                 # Asset upload/management
│   │   │   ├── jobs.py                   # Job submission/status
│   │   │   ├── generation.py             # Video generation endpoints
│   │   │   └── export.py                 # SCORM export functionality
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py                   # User model
│   │   │   ├── asset.py                  # Asset metadata model
│   │   │   ├── job.py                    # Generation job model
│   │   │   └── video.py                  # Generated video model
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py           # JWT/RBAC logic
│   │   │   ├── storage_service.py        # MinIO/S3 operations
│   │   │   ├── zyphra_service.py         # Zyphra TTS API client
│   │   │   ├── kdtalker_service.py       # KDTalker Gradio client
│   │   │   └── ollama_service.py         # Llama-3-8B text generation
│   │   ├── tasks/
│   │   │   ├── __init__.py
│   │   │   ├── celery_app.py             # Celery configuration
│   │   │   ├── voice_tasks.py            # Voice cloning tasks
│   │   │   ├── tts_tasks.py              # Text-to-speech tasks
│   │   │   ├── video_tasks.py            # Video generation tasks
│   │   │   └── export_tasks.py           # SCORM export tasks
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── validators.py             # Input validation
│   │       ├── helpers.py                # Common utilities
│   │       ├── ffmpeg.py                 # Audio/video processing
│   │       └── security.py               # Security utilities
│   ├── migrations/                       # Database migrations
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py                   # Pytest configuration
│   │   ├── test_api/                     # API endpoint tests
│   │   ├── test_services/                # Service layer tests
│   │   ├── test_tasks/                   # Celery task tests
│   │   └── test_utils/                   # Utility function tests
│   ├── requirements.txt                  # Python dependencies
│   ├── app.py                           # Application entry point
│   └── celery_worker.py                 # Celery worker entry point
│
├── ⚛️ Frontend (React + Tailwind)
│   ├── src/
│   │   ├── components/
│   │   │   ├── common/                   # Reusable UI components
│   │   │   │   ├── Button.jsx
│   │   │   │   ├── Modal.jsx
│   │   │   │   ├── FileUpload.jsx
│   │   │   │   └── ProgressBar.jsx
│   │   │   ├── auth/                     # Authentication components
│   │   │   │   ├── LoginForm.jsx
│   │   │   │   └── ProtectedRoute.jsx
│   │   │   ├── assets/                   # Asset management components
│   │   │   │   ├── AssetUploader.jsx
│   │   │   │   ├── AssetLibrary.jsx
│   │   │   │   └── AssetPreview.jsx
│   │   │   ├── generation/               # Video generation components
│   │   │   │   ├── ScriptEditor.jsx
│   │   │   │   ├── VoiceSelector.jsx
│   │   │   │   ├── PortraitSelector.jsx
│   │   │   │   └── GenerationWizard.jsx
│   │   │   └── preview/                  # Video preview components
│   │   │       ├── VideoPlayer.jsx
│   │   │       └── ExportOptions.jsx
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx             # Main dashboard
│   │   │   ├── Login.jsx                 # Login page
│   │   │   ├── Assets.jsx                # Asset management page
│   │   │   ├── Generate.jsx              # Video generation wizard
│   │   │   └── Preview.jsx               # Video preview page
│   │   ├── hooks/
│   │   │   ├── useAuth.js                # Authentication hook
│   │   │   ├── useAssets.js              # Asset management hook
│   │   │   ├── useGeneration.js          # Video generation hook
│   │   │   └── useWebSocket.js           # Real-time updates hook
│   │   ├── services/
│   │   │   ├── api.js                    # Axios API client
│   │   │   ├── auth.js                   # Authentication service
│   │   │   ├── assets.js                 # Asset service
│   │   │   └── generation.js             # Generation service
│   │   ├── utils/
│   │   │   ├── constants.js              # App constants
│   │   │   ├── helpers.js                # Utility functions
│   │   │   └── validation.js             # Form validation
│   │   ├── styles/
│   │   │   └── index.css                 # Tailwind CSS
│   │   ├── App.jsx                       # Main App component
│   │   └── main.jsx                      # React entry point
│   ├── public/
│   │   ├── index.html                    # HTML template
│   │   └── favicon.ico                   # App favicon
│   ├── package.json                      # Node.js dependencies
│   ├── vite.config.js                    # Vite configuration
│   └── tailwind.config.js                # Tailwind CSS configuration
│
├── 🐳 Docker & Infrastructure
│   ├── docker/
│   │   ├── services/
│   │   │   ├── Dockerfile.backend        # Backend container
│   │   │   ├── Dockerfile.frontend       # Frontend container
│   │   │   ├── Dockerfile.worker         # Celery worker container
│   │   │   └── Dockerfile.ollama         # Ollama LLM container
│   │   └── docker-compose.yml            # Multi-service orchestration
│   └── infra/
│       ├── kubernetes/                   # K8s deployment files
│       ├── terraform/                    # Infrastructure as code
│       └── nginx/                        # Reverse proxy configuration
│
├── 📚 Documentation
│   └── docs/
│       ├── api.md                        # API documentation
│       ├── deployment.md                 # Deployment guide
│       ├── development.md                # Development setup
│       └── troubleshooting.md            # Common issues
│
├── 🔧 Scripts & Tools
│   └── scripts/
│       ├── setup.sh                      # Initial setup script
│       ├── dev.sh                        # Development environment
│       ├── test.sh                       # Run tests
│       └── deploy.sh                     # Deployment script
│
└── 📄 Root Files
    ├── README.md                         # Project overview
    ├── LICENSE                           # Software license
    ├── .env.example                      # Environment variables template
    ├── .gitignore                        # Git ignore rules
    └── FOLDER_STRUCTURE.md               # This file
```

## 🎯 Key Design Principles

### 1. **Separation of Concerns**
- Backend handles API, auth, and async processing
- Frontend focuses on user experience
- Docker manages infrastructure and dependencies

### 2. **Modular Architecture**
- Each service has dedicated modules
- Clear boundaries between layers
- Easy to test and maintain

### 3. **Scalability Ready**
- Celery for async processing
- Redis for job queuing
- MinIO for distributed storage
- Kubernetes deployment ready

### 4. **Development Friendly**
- Hot reloading for both frontend and backend
- Comprehensive testing setup
- Docker Compose for local development
- Clear documentation

## 🚀 Next Steps

1. **Initialize Backend**: Set up Flask app factory and basic API structure
2. **Initialize Frontend**: Set up React + Vite + Tailwind configuration
3. **Docker Setup**: Create development Docker Compose configuration
4. **Database Models**: Define PostgreSQL schemas for users, assets, jobs
5. **API Endpoints**: Implement core REST endpoints
6. **Celery Tasks**: Set up async job processing
7. **Frontend Components**: Build reusable UI components
8. **Integration**: Connect frontend to backend APIs
9. **Testing**: Implement unit and integration tests
10. **Documentation**: Complete API and deployment docs
