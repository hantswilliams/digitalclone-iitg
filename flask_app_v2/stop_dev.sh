#!/bin/zsh

# stop_dev.sh - Script to stop all development services

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
  echo "Error: Docker is not running."
  exit 1
fi

echo "Stopping all development services..."

# Get the list of running containers for this compose configuration
CONTAINERS=$(docker-compose -f docker-compose.dev.yml ps -q 2>/dev/null)

if [ -z "$CONTAINERS" ]; then
  echo "No development services are currently running."
else
  # Gracefully stop the containers
  if docker-compose -f docker-compose.dev.yml down; then
    echo "✅ Development services stopped successfully."
  else
    echo "❌ Error stopping development services. You may need to manually stop containers with docker-compose -f docker-compose.dev.yml down --remove-orphans"
  fi
fi

# Check for any leftover containers that might be using the same volume
ORPHANS=$(docker ps -a --filter "name=flask_app_v2" --format "{{.ID}}")
if [ ! -z "$ORPHANS" ]; then
  echo "Warning: Found possibly related containers still running:"
  docker ps -a --filter "name=flask_app_v2"
  echo "You may want to stop these manually with: docker stop [CONTAINER_ID]"
fi

echo "Development environment stopped. You can restart it with ./dev.sh"
