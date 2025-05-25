#!/bin/bash

# Development setup script for Voice-Cloned Talking-Head Lecturer

set -e

echo "🚀 Setting up Voice-Cloned Talking-Head Lecturer development environment..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ Created .env file. Please edit it with your API keys and configuration."
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p backend/app/static/uploads
mkdir -p backend/app/static/generated
mkdir -p backend/logs
mkdir -p frontend/public

# Build and start services
echo "🐳 Building and starting Docker services..."
docker-compose up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if database is ready
echo "🗄️ Checking database connection..."
docker-compose exec -T db pg_isready -U clone_user -d cloneapp

# Initialize database
echo "🔧 Initializing database..."
docker-compose exec backend flask db upgrade || {
    echo "📊 Creating initial migration..."
    docker-compose exec backend flask db init
    docker-compose exec backend flask db migrate -m "Initial migration"
    docker-compose exec backend flask db upgrade
}

# Setup MinIO bucket
echo "🪣 Setting up MinIO bucket..."
docker-compose exec -T minio mc alias set local http://localhost:9000 minioadmin minioadmin
docker-compose exec -T minio mc mb local/voice-clone-assets --ignore-existing

# Pull Ollama model (optional)
echo "🤖 Pulling Ollama model (this may take a while)..."
docker-compose exec ollama ollama pull llama3:8b || echo "⚠️ Ollama model pull failed, will try later"

echo "✅ Development environment setup complete!"
echo ""
echo "🌐 Services available at:"
echo "   Frontend:    http://localhost:3000"
echo "   Backend API: http://localhost:5000"
echo "   MinIO Console: http://localhost:9001 (minioadmin/minioadmin)"
echo "   Flower (Celery): http://localhost:5555"
echo "   Ollama API: http://localhost:11434"
echo ""
echo "📚 Useful commands:"
echo "   docker-compose logs -f                 # View all logs"
echo "   docker-compose logs -f backend         # View backend logs"
echo "   docker-compose exec backend flask shell # Flask shell"
echo "   docker-compose down                    # Stop all services"
echo ""
echo "🎉 Happy coding!"
