#!/bin/zsh

# dev.sh - Script to run the Flask application in development mode

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
  echo "Error: Docker is not running. Please start Docker and try again."
  exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose > /dev/null 2>&1; then
  echo "Error: docker-compose is not installed. Please install docker-compose and try again."
  exit 1
fi

# Load environment variables from .env.dev file
if [ -f .env.dev ]; then
  echo "Loading environment variables from .env.dev..."
  set -a
  source .env.dev
  set +a
else
  echo "Warning: .env.dev file not found. Using default environment variables."
fi

# Export FLASK_APP for flask commands
export FLASK_APP=run.py

# Start the supporting services in the background
echo "Starting Redis and PostgreSQL services..."
docker-compose -f docker-compose.dev.yml up -d db redis

# Wait for services to be ready (more robust check)
echo "Waiting for PostgreSQL to be ready..."
pg_ready=false
for i in {1..10}; do
  if docker-compose -f docker-compose.dev.yml exec db pg_isready -h localhost -U postgres > /dev/null 2>&1; then
    pg_ready=true
    break
  fi
  echo "Waiting for PostgreSQL to start... ($i/10)"
  sleep 2
done

if [ "$pg_ready" = false ]; then
  echo "Error: PostgreSQL did not start properly. Check docker logs with: docker-compose -f docker-compose.dev.yml logs db"
  exit 1
fi

echo "Waiting for Redis to be ready..."
redis_ready=false
for i in {1..5}; do
  if docker-compose -f docker-compose.dev.yml exec redis redis-cli ping > /dev/null 2>&1; then
    redis_ready=true
    break
  fi
  echo "Waiting for Redis to start... ($i/5)"
  sleep 2
done

if [ "$redis_ready" = false ]; then
  echo "Error: Redis did not start properly. Check docker logs with: docker-compose -f docker-compose.dev.yml logs redis"
  exit 1
fi

# Start Celery worker in the background
echo "Starting Celery worker..."
docker-compose -f docker-compose.dev.yml up -d celery_worker

# Install requirements if needed
echo "Checking for required Python packages..."
pip3 install -r requirements.txt

# Database tables will be created automatically when the Flask app starts

# Run the Flask application
echo "Starting Flask application in development mode..."
PORT=${FLASK_PORT:-5002}
echo "Access the application at: http://localhost:$PORT"
echo -e "\n⚠️  To stop all services when done, run: ./stop_dev.sh\n"
python3 run.py
