#!/bin/zsh

# status_dev.sh - Script to check the status of development services

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
  echo "Error: Docker is not running."
  exit 1
fi

echo "Checking development environment status..."
echo "----------------------------------------"

# Check Docker Compose services
echo "DOCKER SERVICES:"
docker-compose -f docker-compose.dev.yml ps

# Check database connection
echo -e "\nDATABASE CONNECTION:"
if docker-compose -f docker-compose.dev.yml exec db pg_isready -h localhost -U postgres > /dev/null 2>&1; then
  echo "✅ PostgreSQL is running and accepting connections"
else
  echo "❌ PostgreSQL is not responding"
fi

# Check Redis connection
echo -e "\nREDIS CONNECTION:"
if docker-compose -f docker-compose.dev.yml exec redis redis-cli ping > /dev/null 2>&1; then
  echo "✅ Redis is running and responding to PING"
else
  echo "❌ Redis is not responding"
fi

# Check Celery worker status
echo -e "\nCELERY WORKER:"
if docker-compose -f docker-compose.dev.yml logs --tail=10 celery_worker | grep "ready" > /dev/null; then
  echo "✅ Celery worker appears to be running"
else
  echo "⚠️ Celery worker status is unclear, check logs with: docker-compose -f docker-compose.dev.yml logs celery_worker"
fi

# Print connection information
echo -e "\nCONNECTION INFORMATION:"
if [ -f .env.dev ]; then
  PORT=$(grep FLASK_PORT .env.dev | cut -d= -f2 || echo "5002")
else
  PORT="5002"
fi
echo "- Flask App URL: http://localhost:$PORT"
echo "- PostgreSQL: localhost:5433 (User: postgres, Password: postgres, DB: digitalclone)"
echo "- Redis: localhost:6380"

echo -e "\nHELPFUL COMMANDS:"
echo "- Start development environment: ./dev.sh"
echo "- Stop development environment: ./stop_dev.sh"
echo "- View logs: docker-compose -f docker-compose.dev.yml logs [service_name]"
echo "- Connect to database: psql -h localhost -p 5433 -U postgres -d digitalclone"
