# Development Stage Planning

## Completed ✅

| Stage                        | Status | Focus                     | Deliverables                                                                                           | 
| ---------------------------- | ------ | ------------------------- | ------------------------------------------------------------------------------------------------------ |
| **0 Bootstrap**              | ✅     | *Flask shell*             | `backend/app/__init__.py`, `config.py`, application factory, `docker-compose.yml` with Postgres & Redis |
| **1 Auth & RBAC**            | ✅     | JWT login + roles         | **COMPLETED**: `/api/auth/*` endpoints, User model, JWT tokens, validation, RBAC decorators, test scripts |
| **2 Asset ingest**           | ✅     | Portrait & audio uploads  | **COMPLETED**: `/api/assets` endpoints, MinIO integration, presigned URLs, Asset model, comprehensive testing |
| **3 Job schema**             | ✅     | Job tracking tables       | **COMPLETED**: `Job` and `JobStep` models, `/api/jobs` CRUD endpoints, progress tracking, comprehensive testing |
| **4 Celery + Redis**         | ✅     | Background queue          | **COMPLETED**: Redis connectivity, Celery workers, task registration, `/api/worker/*` endpoints, health checks |
| **5 Zyphra service wrapper** | ✅     | Voice cloning + TTS       | **COMPLETED**: Zyphra API client, TTS Celery tasks, `/api/generate/text-to-speech` endpoint, comprehensive testing |
| **6 KDTalker wrapper**       | ✅     | Portrait-to-video         | **COMPLETED**: KDTalker client, video Celery tasks, `/api/generate/video` endpoint, comprehensive testing |
| **7 LLM service**            | ✅     | Script generation         | **COMPLETED**: Llama-4 client, script Celery tasks, `/api/generate/script` endpoint, comprehensive testing |

## In Progress / Pending

| Stage                        | Status | Focus                     | Deliverables                                                                                           |
| ---------------------------- | ------ | ------------------------- | ------------------------------------------------------------------------------------------------------ |
| **8 Realtime updates**       | ⏳     | WebSocket or SSE          | `/ws/jobs/{id}`; front-end progress bar; broadcast Celery events                                        |
| **9 React UI MVP**           | ⏳     | Upload → prompt → preview | Pages: Login, Dashboard, New Video Wizard, Job History, Settings; Tailwind components                   |
| **10 Export & LMS**          | ⏳     | SCORM/MP4 download        | `services/export/scorm.py`; "Download" & "Embed" buttons                                                |
| **11 CI/CD**                 | ⏳     | Tests + containers        | GitHub Actions: flake8, pytest, Cypress, Docker build; `docker-compose.prod.yml`                        |

## Stage 1 Completion Details ✅

### Authentication System Implementation
- **User Registration**: Email validation, password strength, username format checking
- **User Login**: JWT access & refresh tokens, remember me functionality
- **Token Management**: Refresh tokens, secure logout with blacklisting
- **Profile Management**: View/update profile, change password with validation
- **Security Features**: RBAC decorators, password hashing, token revocation
- **Database Models**: Complete User model with relationships and enums
- **Validation Schemas**: Comprehensive Marshmallow schemas for all endpoints
- **Error Handling**: Proper HTTP status codes and structured error responses
- **Test Infrastructure**: Automated test script, database init scripts, dev server script

### Scripts Created
- `scripts/init_db.py` - Database initialization with default admin user
- `scripts/run_dev.py` - Development server with endpoint documentation  
- `scripts/test_auth.py` - Comprehensive authentication endpoint testing

## Stage 2 Completion Details ✅

### Asset Management System Implementation
- **File Upload Endpoints**: Traditional multipart/form-data upload for portraits, voice samples, and scripts
- **Presigned URL Workflow**: Secure S3-style presigned URLs for direct client-to-storage uploads
- **Storage Integration**: MinIO object storage with proper bucket management and file organization
- **Asset Management**: Complete CRUD operations (Create, Read, Update, Delete) for assets
- **File Validation**: Content-type validation, file size limits, allowed extensions per asset type
- **Asset Filtering**: Query assets by type, status, and other metadata
- **Download URLs**: Secure presigned download URLs with expiration
- **Database Models**: Asset model with relationships to users and proper status tracking
- **Error Handling**: Graceful handling of storage failures and invalid requests
- **Security**: JWT-protected endpoints with user isolation (users only see their own assets)

### Features Implemented
- **Asset Types**: Support for portraits (images), voice samples (audio), and scripts (text)
- **Upload Confirmation**: Two-stage upload process for presigned URLs with confirmation step
- **Metadata Tracking**: File size, content type, upload timestamp, and status tracking
- **Pagination**: Efficient asset listing with pagination support
- **Status Management**: Asset status lifecycle (pending, ready, processing, failed)

### Scripts Created
- `scripts/test_assets.py` - Comprehensive asset management testing (13/13 tests passing)

## Stage 4 Completion Details ✅

### Celery + Redis Background Processing Implementation
- **Redis Integration**: Successfully connected Redis broker on port 6379 with read/write operations
- **Celery Configuration**: Updated to modern configuration format (broker_url, result_backend vs deprecated CELERY_* settings)
- **Task Registration**: Implemented and registered multiple tasks including echo_task with progress tracking
- **Worker Management**: Created comprehensive worker management API endpoints
- **Health Monitoring**: Real-time worker status, active/scheduled task monitoring
- **Authentication Integration**: JWT-protected worker endpoints with proper authentication flow
- **Background Processing**: Verified end-to-end task queuing, processing, and result tracking

### API Endpoints Implemented
- `/api/worker/ping` - Basic health check endpoint
- `/api/worker/status` - Detailed worker information with active/scheduled tasks
- `/api/worker/test-echo` - JWT-protected echo task trigger for testing
- `/api/worker/task/<task_id>` - Task status and result tracking

### Features Implemented
- **Task Progress Tracking**: Multi-step progress reporting with worker PID and status updates
- **Worker Discovery**: Automatic detection of active Celery workers and their capabilities
- **Error Handling**: Proper error propagation from workers to API consumers
- **Configuration Management**: Centralized Celery configuration with environment-based settings
- **Integration Testing**: Comprehensive test script validating Redis, Celery, and API functionality

### Infrastructure Components
- **Redis Broker**: Docker container with persistent data and proper networking
- **Celery Workers**: Background worker processes with task discovery and execution
- **Task Queues**: Default queue configuration with expansion capability for specialized workers
- **Monitoring**: Worker inspection and task state monitoring capabilities

### Scripts Created
- `test_celery_redis.py` - Complete integration testing (7/7 tests passing)
- `celery_app.py` - Dedicated worker entry point with proper task imports

## Stage 3 Completion Details ✅

### Job Schema and Management System Implementation
- **Job Models**: Complete Job and JobStep models with comprehensive status tracking and relationships
- **Database Schema**: Full job tracking tables with proper foreign keys and constraints
- **Job Management API**: CRUD operations for jobs with filtering, pagination, and sorting
- **Job Types**: Support for voice_clone, text_to_speech, video_generation, and full_pipeline workflows
- **Status Management**: Job lifecycle tracking (pending, running, completed, failed, cancelled)
- **Progress Tracking**: Real-time progress updates with percentage and message tracking
- **Priority System**: Job priority levels (low, normal, high, urgent) with queue management
- **Error Handling**: Comprehensive error tracking and validation for all job operations
- **Authentication Integration**: JWT-protected job endpoints with user isolation
- **Data Validation**: Marshmallow schemas for job creation, updates, and responses

### API Endpoints Implemented
- `/api/jobs` - Create new jobs with type-specific parameters
- `/api/jobs` (GET) - List jobs with filtering by type, status, priority, pagination
- `/api/jobs/<id>` - Get detailed job information including steps and progress
- `/api/jobs/<id>` (PUT) - Update job priority, description, and metadata
- `/api/jobs/<id>/cancel` - Cancel running or pending jobs
- `/api/jobs/<id>/progress` - Update job progress with percentage and messages

### Features Implemented
- **Job Creation**: Support for all job types with proper parameter validation
- **Job Filtering**: Query jobs by type, status, priority with pagination support
- **Progress Simulation**: Multi-step job processing simulation with realistic progress tracking
- **Job Cancellation**: Proper job state management for cancelled jobs
- **Database Migrations**: Proper Alembic migrations for job schema
- **Input Validation**: Comprehensive validation for job parameters and updates
- **Error Recovery**: Graceful handling of invalid requests and database errors

### Scripts Created
- `scripts/test_jobs.py` - Comprehensive job management testing (10/10 tests passing)

## Stage 5 Completion Details ✅

### Zyphra TTS Service Integration Implementation
- **Zyphra API Client**: Complete `ZyphraClient` class with authentication, voice cloning, and TTS generation
- **Service Configuration**: Environment-based API key management and URL configuration
- **Audio Processing**: Base64 encoding/decoding for API communication and format conversion
- **Health Monitoring**: Service validation and connectivity testing with error handling
- **Error Management**: Comprehensive error handling with proper status codes and messaging
- **Configuration Validation**: API key validation and service health checking

### Celery Tasks Implementation
- **Speech Generation**: `generate_speech()` task with job progress tracking and MinIO storage
- **Service Validation**: `validate_tts_service()` task for health checking and status monitoring
- **Audio Conversion**: `convert_audio_format()` task for WebM to WAV conversion using FFmpeg
- **Progress Tracking**: Real-time job status updates with percentage progress and error handling
- **Storage Integration**: Automatic MinIO storage with secure object naming and access
- **Task Registration**: Proper Celery task imports and worker discovery

### API Endpoints Implementation
- **Text-to-Speech**: `/api/generate/text-to-speech` - Create TTS jobs with voice asset validation
- **Service Status**: `/api/generate/tts/status` - Real-time TTS service health and status checking
- **Request Validation**: Marshmallow schemas for TTS requests with text and voice asset validation
- **JWT Authentication**: Secure endpoints with user authentication and authorization
- **Error Handling**: Comprehensive error responses with proper HTTP status codes
- **Job Integration**: Full integration with job tracking system and Celery task queue

### Features Implemented
- **Voice Cloning**: Text-to-speech generation using uploaded voice samples via Zyphra API
- **Audio Format Support**: WebM output from Zyphra with WAV conversion for downstream processing
- **Job Management**: Full job lifecycle tracking from creation to completion with progress updates
- **Service Monitoring**: Real-time health checking and service status validation
- **Security**: JWT-protected endpoints with user isolation and voice asset ownership validation
- **Storage Management**: Secure MinIO storage for generated audio files with proper access control

### Technical Components
- **Zyphra Client**: `/app/services/tts/zyphra_client.py` - Complete API client (200+ lines)
- **TTS Tasks**: `/app/tasks/tts_tasks.py` - Celery tasks for speech generation and validation
- **API Endpoints**: `/app/api/generation.py` - REST endpoints for TTS functionality
- **Test Infrastructure**: `test_zyphra_tts.py` - Comprehensive testing suite (4/4 tests passing)
- **Environment Configuration**: Proper API key management and service URL configuration
- **Audio Processing**: FFmpeg integration for audio format conversion and validation

### Testing Results
- **Zyphra Client Configuration**: ✅ PASS - API key validation and client initialization
- **Audio Format Conversion**: ✅ PASS - WebM to WAV conversion using FFmpeg
- **TTS Validation Task**: ✅ PASS - Service health checking via Celery tasks
- **API Endpoints**: ✅ PASS - Authentication, TTS job creation, and status monitoring

### Scripts Created
- `test_zyphra_tts.py` - Comprehensive TTS integration testing (4/4 tests passing)

### Integration Notes
- **Database**: Uses SQLite for development with PostgreSQL support for production
- **Redis/Celery**: Full integration with background task processing and progress tracking
- **MinIO Storage**: Secure object storage for generated audio files with presigned URLs
- **Authentication**: JWT-based authentication with proper user isolation and security
- **Error Handling**: Graceful degradation when Zyphra service is unavailable with proper status reporting

## Stage 6 Completion Details ✅

### KDTalker Video Generation Implementation
- **KDTalker Client**: `/app/services/video/kdtalker_client.py` - Remote Hugging Face Spaces integration (280+ lines)
- **Video Tasks**: `/app/tasks/video_tasks.py` - Celery tasks for video generation and thumbnail creation
- **API Endpoints**: `/app/api/generation.py` - REST endpoints for video generation functionality
- **Test Infrastructure**: `test_kdtalker_video.py` - Comprehensive testing suite (4/4 tests passing)
- **Environment Configuration**: Hugging Face Spaces integration via gradio_client
- **Video Processing**: Portrait-to-video generation with configurable parameters

### Key Features Implemented
- **Remote Service Integration**: Uses KDTalker via Hugging Face Spaces (fffiloni/KDTalker)
- **Video Configuration**: Support for enhancers (gfpgan), FPS settings, face enhancement, preprocessing
- **Asset Management**: Portrait and audio asset validation with proper status checking
- **Job Management**: Full job lifecycle with title, description, progress tracking, and error handling
- **Background Processing**: Celery integration for async video generation tasks
- **Storage Integration**: MinIO/S3 storage for input assets and output video files

### Testing Results
- **KDTalker Client Configuration**: ✅ PASS - Remote service connectivity and health checking
- **Video Service Validation**: ✅ PASS - Service status validation via Celery tasks
- **Create Test Assets**: ✅ PASS - Portrait and audio asset creation and upload
- **Video Generation API**: ✅ PASS - Job creation, task queuing, and progress monitoring

### Technical Achievements
- **Enum Standardization**: Fixed AssetStatus and JobStatus enum comparisons throughout codebase
- **Database Models**: Proper Job model integration with title requirements and enum values
- **JSON Serialization**: Correct enum value serialization for API responses
- **Error Handling**: Comprehensive validation of asset ownership, status, and types
- **API Integration**: RESTful endpoints with JWT authentication and proper error responses

### Scripts Created
- `test_kdtalker_video.py` - Comprehensive video generation testing (4/4 tests passing)

### Integration Notes
- **Remote Dependencies**: Uses Hugging Face Spaces for video generation (no local GPU required)
- **Asset Pipeline**: Full integration with asset upload, validation, and storage systems
- **Job System**: Complete integration with Stage 3 job management and progress tracking
- **Background Tasks**: Celery worker integration for scalable video processing
- **Authentication**: JWT-based user isolation and asset ownership validation

## Stage 7 Completion Details ✅

### LLM Script Generation Implementation
- **Llama-4 Client**: `/app/services/llm/llama_client.py` - Remote Hugging Face Spaces integration (287+ lines)
- **LLM Tasks**: `/app/tasks/llm_tasks.py` - Celery tasks for script generation and service validation (235+ lines)
- **API Endpoints**: `/app/api/generation.py` - REST endpoints for script generation functionality
- **Test Infrastructure**: `test_llm_script.py` and `quick_llm_test.py` - Comprehensive testing suites
- **Environment Configuration**: Hugging Face Spaces integration via gradio_client with Llama-4-Scout-17B-Research
- **Request Validation**: Marshmallow schemas for script generation with comprehensive parameter validation

### Key Features Implemented
- **Remote LLM Integration**: Uses Llama-4 via Hugging Face Spaces (openfree/Llama-4-Scout-17B-Research)
- **Script Configuration**: Support for prompts, topics, target audiences, duration, styles, and additional context
- **Job Management**: Full job lifecycle with title, description, progress tracking, and error handling
- **Background Processing**: Celery integration for async script generation tasks
- **Health Monitoring**: LLM service validation and connectivity testing
- **Parameter Validation**: Comprehensive input validation for script generation requests

### API Endpoints Implemented
- **Script Generation**: `/api/generate/script` - Create script generation jobs with comprehensive parameter validation
- **Service Status**: `/api/generate/llm/status` - Real-time LLM service health and status checking
- **Request Validation**: Marshmallow schemas for script requests with style, audience, and content validation
- **JWT Authentication**: Secure endpoints with user authentication and authorization
- **Error Handling**: Comprehensive error responses with proper HTTP status codes
- **Job Integration**: Full integration with job tracking system and Celery task queue

### Technical Components
- **LlamaClient**: Complete client with health checking, script generation, and prompt building capabilities
- **LlamaConfig**: Configuration management with validation and environment integration
- **Script Analysis**: Word count, character count, and duration estimation capabilities
- **Progress Tracking**: Real-time job status updates with percentage progress and messaging
- **Error Management**: Comprehensive error handling with proper status codes and user feedback

### Testing Results
- **Authentication**: ✅ PASS - User authentication successful
- **Script Generation Request**: ✅ PASS - Job creation, task queuing, and progress monitoring
- **Request Validation**: ✅ PASS - Proper validation for missing/invalid parameters
- **Service Health**: ✅ PASS - LLM service connectivity and health checking

### Integration Notes
- **Remote Dependencies**: Uses Hugging Face Spaces for LLM processing (no local GPU required)
- **Job System**: Complete integration with Stage 3 job management and progress tracking
- **Background Tasks**: Celery worker integration for scalable script processing
- **Authentication**: JWT-based user isolation and secure access control
- **Parameter Flexibility**: Support for various script styles, audiences, and content customization

### Scripts Created
- `test_llm_script.py` - Comprehensive LLM integration testing with full workflow validation
- `quick_llm_test.py` - Fast testing for core LLM functionality verification
- `run_celery.py` - Celery worker runner with proper Flask app context

### Technical Achievements
- **JobType Extension**: Added SCRIPT_GENERATION to job type enumeration for proper classification
- **API Standardization**: Consistent REST API patterns following existing TTS and video generation endpoints
- **Schema Validation**: Comprehensive Marshmallow schemas for all script generation parameters with proper OneOf validation
- **Service Monitoring**: Real-time health checking and service status validation for remote dependencies
- **Error Handling**: Graceful degradation when Hugging Face Spaces is unavailable with proper status reporting
- **Storage Integration**: Complete MinIO storage integration with asset tracking and presigned URL generation
- **Metadata Extraction**: Automatic word count, character count, and duration estimation for generated scripts

### Storage and Retrieval Functionality ✅
- **Script Storage**: Generated scripts saved to MinIO object storage with proper file organization and security
- **Asset Tracking**: Scripts linked to jobs as assets with full audit trail and metadata
- **Content Retrieval**: Script content accessible via job results API and asset download endpoints
- **Metadata Access**: Word count, character count, and estimated duration available through job results
- **Download URLs**: Secure presigned URLs for script file downloads with proper authentication
- **Progress Monitoring**: Real-time job status updates with script generation progress tracking

### Final Testing Status ✅
- **Test 1 - Authentication**: ✅ PASS - JWT token-based user authentication
- **Test 2 - LLM Health Check**: ✅ PASS - Hugging Face Spaces connectivity and service validation
- **Test 3 - Script Generation Request**: ✅ PASS - Job creation with proper parameter handling
- **Test 4 - Progress Monitoring**: ✅ PASS - Real-time job status and completion tracking
- **Test 5 - Request Validation**: ✅ PASS - Proper validation for required fields and invalid parameters
- **Integration Verified**: ✅ Script generation, storage, and retrieval working end-to-end
- **Quality Metrics**: Generated scripts average 586+ words with 3.9+ minute estimated duration

### Date Completed
**May 26, 2025** - All Stage 7 objectives completed with comprehensive testing validation

---

## Stage 9: React UI MVP Planning 🚀

### Overview
Build a modern, responsive React frontend using Tailwind CSS for the voice clone talking head application. The UI will provide a complete user experience from authentication through video generation, with smart polling for real-time updates.

### Core User Journey
```
Login → Dashboard → Upload Assets → Generate Content → Create Video → Download/Share
```

### Technology Stack
- **Frontend Framework**: React 18+ with hooks
- **Styling**: Tailwind CSS with custom component library
- **State Management**: React Context + useReducer for complex state
- **Routing**: React Router v6
- **HTTP Client**: Axios with interceptors for auth
- **File Upload**: React Dropzone for drag-and-drop
- **Forms**: React Hook Form with validation
- **Progress Updates**: Smart polling strategy (no WebSockets for MVP)

### Backend API Integration Map

#### Authentication Endpoints
**Base URL**: `http://localhost:5001/api/auth`

| Frontend Component | API Endpoint | Method | Purpose |
|-------------------|--------------|--------|---------|
| `LoginPage.jsx` | `/api/auth/login` | POST | User authentication with JWT tokens |
| `RegisterPage.jsx` | `/api/auth/register` | POST | New user account creation |
| `Header.jsx` (logout) | `/api/auth/logout` | POST | Token invalidation and logout |
| `Header.jsx` (refresh) | `/api/auth/refresh` | POST | Refresh access token |
| `SettingsPage.jsx` | `/api/auth/profile` | GET/PUT | View/update user profile |
| `SettingsPage.jsx` | `/api/auth/change-password` | PUT | Password change functionality |

#### Asset Management Endpoints  
**Base URL**: `http://localhost:5001/api/assets`

| Frontend Component | API Endpoint | Method | Purpose |
|-------------------|--------------|--------|---------|
| `AssetsPage.jsx` | `/api/assets` | GET | List user's assets by type with pagination |
| `AssetUpload.jsx` | `/api/assets/presigned-url` | POST | Get presigned URL for direct upload |
| `AssetUpload.jsx` | `[presigned-url]` | PUT | Direct upload to MinIO storage |
| `AssetUpload.jsx` | `/api/assets` | POST | Register uploaded asset with metadata |
| `AssetCard.jsx` | `/api/assets/{id}` | PUT | Update asset metadata (rename, description) |
| `AssetCard.jsx` | `/api/assets/{id}` | DELETE | Delete asset and storage file |
| `AssetCard.jsx` | `/api/assets/{id}` | GET | Get asset details with download URL |
| `Step1_SelectPhoto.jsx` | `/api/assets?type=portrait` | GET | Get user's portrait images |
| `Step3_SelectVoice.jsx` | `/api/assets?type=voice_sample` | GET | Get user's voice samples |

#### Job Management Endpoints
**Base URL**: `http://localhost:5001/api/jobs`

| Frontend Component | API Endpoint | Method | Purpose |
|-------------------|--------------|--------|---------|
| `DashboardPage.jsx` | `/api/jobs?limit=5&status=active` | GET | Recent jobs overview |
| `JobsPage.jsx` | `/api/jobs` | GET | All user jobs with pagination & filtering |
| `JobDetailPage.jsx` | `/api/jobs/{id}` | GET | Detailed job information with steps |
| `ProgressTracker.jsx` | `/api/jobs/{id}` | GET | Real-time job progress polling |
| `CreateVideoPage.jsx` | `/api/jobs` | POST | Create new video generation job |
| `JobCard.jsx` | `/api/jobs/{id}/cancel` | POST | Cancel running job |
| `JobCard.jsx` | `/api/jobs/{id}` | PUT | Update job metadata |
| `JobDetailPage.jsx` | `/api/jobs/{id}/steps` | GET | Get all steps for a job |
| `JobDetailPage.jsx` | `/api/jobs/{id}/steps` | POST | Create new job step |

#### Content Generation Endpoints
**Base URL**: `http://localhost:5001/api/generate`

| Frontend Component | API Endpoint | Method | Purpose |
|-------------------|--------------|--------|---------|
| `Step2_CreateScript.jsx` | `/api/generate/script` | POST | Generate script using LLM |
| `Step3_SelectVoice.jsx` | `/api/generate/tts` | POST | Generate audio from text using TTS |
| `Step4_GenerateVideo.jsx` | `/api/generate/video` | POST | Generate talking-head video |
| `SettingsPage.jsx` | `/api/generate/tts/validate` | GET | Check TTS service availability |
| `SettingsPage.jsx` | `/api/generate/video/validate` | GET | Check video generation service status |
| `SettingsPage.jsx` | `/api/generate/llm/validate` | GET | Check LLM service connectivity |

#### Worker & System Status Endpoints
**Base URL**: `http://localhost:5001/api/worker`

| Frontend Component | API Endpoint | Method | Purpose |
|-------------------|--------------|--------|---------|
| `DashboardPage.jsx` | `/api/worker/status` | GET | Celery worker health & queue status |
| `SettingsPage.jsx` | `/api/worker/ping` | GET | Quick worker ping for health checks |
| `JobDetailPage.jsx` | `/api/worker/task/{task_id}` | GET | Get specific Celery task status |

#### Health Check
**Base URL**: `http://localhost:5001`

| Frontend Component | API Endpoint | Method | Purpose |
|-------------------|--------------|--------|---------|
| `App.jsx` (startup) | `/health` | GET | API server health check |

#### Error Handling Strategy
- **401 Unauthorized**: Redirect to login page, clear auth tokens
- **403 Forbidden**: Show permission denied message
- **404 Not Found**: Show resource not found message  
- **422 Validation Error**: Display field-specific validation errors
- **429 Rate Limited**: Show rate limit message with retry timer
- **500 Server Error**: Show generic error with retry option
- **502/503 Service Unavailable**: Show maintenance mode message
- **Network Errors**: Show connectivity issues with retry

#### Authentication Flow
```javascript
// JWT Token Management
1. Login → Store access_token + refresh_token
2. API Requests → Include Bearer token in headers
3. Token Refresh → Auto-refresh on 401 responses
4. Logout → Clear tokens + call logout endpoint
```

### Page Structure & Components

#### 1. Authentication Pages
**Location**: `src/pages/auth/`

- **`LoginPage.jsx`**
  - Email/password form with validation
  - Remember me checkbox
  - Forgot password link (placeholder)
  - Clean form with Tailwind styling

- **`RegisterPage.jsx`**
  - User registration form
  - Email, username, password validation
  - Terms acceptance
  - Auto-redirect to login after success

#### 2. Main Application Layout
**Location**: `src/components/layout/`

- **`AppLayout.jsx`**
  - Main app shell with sidebar navigation
  - Header with user profile dropdown
  - Responsive design (mobile-first)
  - Toast notification system

- **`Sidebar.jsx`**
  - Navigation menu
  - Active state indicators
  - Collapsible on mobile

- **`Header.jsx`**
  - User avatar and name
  - Logout functionality
  - Breadcrumb navigation

#### 3. Dashboard & Overview
**Location**: `src/pages/dashboard/`

- **`DashboardPage.jsx`**
  - Welcome message with user stats
  - Recent jobs overview (last 5)
  - Quick action buttons
  - Usage statistics cards

- **`JobCard.jsx`** (Component)
  - Job status with progress bar
  - Estimated time remaining
  - Quick actions (view, download, retry)
  - Status indicators with icons

#### 4. Asset Management
**Location**: `src/pages/assets/`

- **`AssetsPage.jsx`**
  - Tabbed interface: Photos | Voice Samples | Scripts
  - Grid view of assets with thumbnails
  - Upload button prominently placed
  - Search and filter capabilities

- **`AssetUpload.jsx`** (Component)
  - Drag-and-drop upload zone
  - File type validation
  - Upload progress indicator
  - Preview functionality

- **`AssetCard.jsx`** (Component)
  - Asset thumbnail/preview
  - Metadata display (size, date, type)
  - Actions menu (rename, delete, use)
  - Usage history

#### 5. Content Generation Wizard
**Location**: `src/pages/create/`

- **`CreateVideoPage.jsx`**
  - Multi-step wizard interface
  - Progress indicator at top
  - Navigation between steps
  - Save draft functionality

- **`Step1_SelectPhoto.jsx`**
  - Photo selection from uploaded assets
  - Upload new photo option
  - Preview selected photo
  - Photo validation feedback

- **`Step2_CreateScript.jsx`**
  - Tabbed interface: "Generate with AI" | "Write Manually"
  - AI tab: Topic, audience, style selectors
  - Manual tab: Rich text editor
  - Character count and duration estimate

- **`Step3_SelectVoice.jsx`**
  - Voice sample selection
  - Upload new voice sample option
  - Voice preview player
  - Voice sample validation

- **`Step4_GenerateVideo.jsx`**
  - Final review of all selections
  - Generate button with confirmation
  - Job submission with immediate feedback

#### 6. Jobs & Progress Tracking
**Location**: `src/pages/jobs/`

- **`JobsPage.jsx`**
  - List of all user jobs
  - Filter by status, date, type
  - Pagination for large lists
  - Bulk actions support

- **`JobDetailPage.jsx`**
  - Detailed job information
  - Real-time progress updates
  - Step-by-step progress visualization
  - Error details and retry options

- **`ProgressTracker.jsx`** (Component)
  - Visual progress bar with percentage
  - Current step indicator
  - Estimated time remaining
  - Status messages

#### 7. Results & Downloads
**Location**: `src/pages/results/`

- **`ResultsPage.jsx`**
  - Video player for generated content
  - Download options (MP4, etc.)
  - Share functionality
  - Regenerate options

- **`VideoPlayer.jsx`** (Component)
  - Custom video player with controls
  - Fullscreen support
  - Download button overlay

#### 8. Settings & Profile
**Location**: `src/pages/settings/`

- **`SettingsPage.jsx`**
  - User profile editing
  - Account settings
  - Usage statistics
  - API key management (future)

### Shared Components Library
**Location**: `src/components/ui/`

#### Form Components
- **`Button.jsx`** - Primary, secondary, danger variants
- **`Input.jsx`** - Text, email, password inputs with validation
- **`Select.jsx`** - Dropdown with search capability
- **`FileUpload.jsx`** - Drag-and-drop file upload
- **`TextArea.jsx`** - Multi-line text input

#### Feedback Components
- **`Toast.jsx`** - Success, error, info notifications
- **`ProgressBar.jsx`** - Animated progress indicator
- **`Spinner.jsx`** - Loading indicators
- **`Alert.jsx`** - Warning, error, info alerts

#### Layout Components
- **`Card.jsx`** - Content containers
- **`Modal.jsx`** - Overlay dialogs
- **`Tabs.jsx`** - Tabbed interfaces
- **`Badge.jsx`** - Status indicators

### State Management Strategy

#### Context Providers
```javascript
// src/contexts/
AuthContext.js     // User authentication state
JobContext.js      // Current jobs and polling
AssetContext.js    // User assets and uploads
UIContext.js       // Global UI state (modals, toasts)
```

#### Custom Hooks
```javascript
// src/hooks/
useAuth.js         // Authentication logic
usePolling.js      // Smart polling for job updates
useFileUpload.js   // File upload with progress
useAssets.js       // Asset management
```

### API Integration
**Location**: `src/services/`

- **`api.js`** - Axios configuration with interceptors
- **`authService.js`** - Authentication API calls
- **`assetService.js`** - Asset upload/management
- **`jobService.js`** - Job creation and monitoring
- **`generationService.js`** - Content generation APIs

### Smart Polling Implementation

```javascript
// usePolling hook strategy
const useJobPolling = (jobId) => {
  const [status, setStatus] = useState('pending');
  const [progress, setProgress] = useState(0);
  
  useEffect(() => {
    if (!jobId) return;
    
    const poll = async () => {
      try {
        const response = await jobService.getStatus(jobId);
        setStatus(response.status);
        setProgress(response.progress);
        
        // Stop polling on completion
        if (['completed', 'failed'].includes(response.status)) {
          return;
        }
        
        // Adaptive polling interval
        const interval = response.status === 'processing' ? 2000 : 5000;
        setTimeout(poll, interval);
      } catch (error) {
        console.error('Polling error:', error);
        setTimeout(poll, 10000); // Retry on error
      }
    };
    
    poll();
  }, [jobId]);
  
  return { status, progress };
};
```

### Responsive Design Strategy

#### Breakpoints (Tailwind)
- **Mobile**: `< 640px` - Single column, stacked layout
- **Tablet**: `640px - 1024px` - Two column layout
- **Desktop**: `> 1024px` - Full sidebar + main content

#### Key Responsive Features
- Collapsible sidebar on mobile
- Touch-friendly upload zones
- Mobile-optimized forms
- Responsive video player
- Stack cards on small screens

### File Upload Strategy

#### Drag-and-Drop Zones
- Visual feedback on hover/drag
- File type validation with clear errors
- Upload progress with cancel option
- Preview generation for images
- Audio waveform preview for voice samples

#### Upload Flow
1. **Client Validation** - File type, size, format
2. **Presigned URL Request** - Get secure upload URL
3. **Direct Upload** - Upload to MinIO via presigned URL
4. **Asset Registration** - Register asset with backend
5. **Confirmation** - Show success state and preview

### Error Handling & User Feedback

#### Error States
- **Network Errors** - Retry buttons with exponential backoff
- **Validation Errors** - Inline form validation
- **Upload Errors** - Clear error messages with solutions
- **Job Failures** - Detailed error info with retry options

#### Success Feedback
- **Toast Notifications** - Non-intrusive success messages
- **Progress Indicators** - Clear progress visualization
- **Completion Celebrations** - Satisfying completion animations

### Development Phases

#### Phase 1: Foundation (Week 1)
- [ ] Set up React project with Tailwind
- [ ] Create basic layout components
- [ ] Implement authentication pages
- [ ] Set up routing and context providers

#### Phase 2: Core Features (Week 2)
- [ ] Build asset management pages
- [ ] Implement file upload functionality
- [ ] Create content generation wizard
- [ ] Add job tracking and polling

#### Phase 3: Polish & UX (Week 3)
- [ ] Add animations and micro-interactions
- [ ] Implement error handling
- [ ] Mobile responsiveness testing
- [ ] Performance optimization

#### Phase 4: Integration (Week 4)
- [ ] End-to-end testing
- [ ] Backend integration testing
- [ ] User acceptance testing
- [ ] Documentation and deployment prep

### Future Enhancements (Post-MVP)
- **Real-time Updates** - WebSocket integration for instant updates
- **SCORM Export** - PowerPoint and SCORM package generation
- **Team Features** - Sharing and collaboration
- **Advanced Editor** - Rich text editing with formatting
- **Templates** - Pre-built content templates
- **Analytics** - Usage analytics and insights

### Success Metrics
- **User Onboarding** - < 2 minutes from registration to first video
- **Upload Experience** - < 30 seconds for asset upload
- **Generation Flow** - < 5 minutes from start to video generation
- **Mobile Experience** - Fully functional on mobile devices
- **Error Recovery** - Clear error messages with actionable solutions

### Date Target
**Start Date**: May 26, 2025  
**MVP Completion Target**: June 23, 2025 (4 weeks)  
**Beta Launch**: July 7, 2025

---
