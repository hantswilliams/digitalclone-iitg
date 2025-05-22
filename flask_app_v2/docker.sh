#!/bin/bash

# Docker management script for flask_app_v2

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored messages
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_message "$RED" "Docker is not installed. Please install Docker before running this script."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_message "$RED" "Docker Compose is not installed. Please install Docker Compose before running this script."
    exit 1
fi

# Check if .env file exists, create from example if not
if [ ! -f ".env" ]; then
    print_message "$YELLOW" ".env file not found. Creating from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_message "$GREEN" "Created .env file from .env.example. Please edit it with your configuration."
    else
        print_message "$RED" ".env.example file not found. Please create a .env file manually."
        exit 1
    fi
fi

# Function to display usage
show_usage() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  dev       - Start development environment"
    echo "  prod      - Start production environment"
    echo "  stop      - Stop running containers"
    echo "  restart   - Restart containers"
    echo "  logs      - View logs"
    echo "  clean     - Remove containers, images, and volumes"
    echo "  shell     - Open shell in web container"
    echo "  status    - Check container status"
    echo "  help      - Show this help message"
}

# Function to start development environment
start_dev() {
    print_message "$GREEN" "Starting development environment..."
    docker-compose up -d
    print_message "$GREEN" "Development environment started at http://localhost:5001"
}

# Function to start production environment
start_prod() {
    print_message "$GREEN" "Starting production environment..."
    docker-compose -f docker-compose.prod.yml up -d
    print_message "$GREEN" "Production environment started at http://localhost:5000"
}

# Function to stop containers
stop_containers() {
    print_message "$YELLOW" "Stopping containers..."
    docker-compose down
    print_message "$GREEN" "Containers stopped."
}

# Function to restart containers
restart_containers() {
    print_message "$YELLOW" "Restarting containers..."
    if [ "$1" == "prod" ]; then
        docker-compose -f docker-compose.prod.yml restart
    else
        docker-compose restart
    fi
    print_message "$GREEN" "Containers restarted."
}

# Function to view logs
view_logs() {
    if [ "$1" == "prod" ]; then
        docker-compose -f docker-compose.prod.yml logs -f
    else
        docker-compose logs -f
    fi
}

# Function to clean up
clean_up() {
    print_message "$YELLOW" "Removing containers, images, and volumes..."
    docker-compose down -v --rmi local
    print_message "$GREEN" "Clean up complete."
}

# Function to open shell in web container
open_shell() {
    if [ "$1" == "prod" ]; then
        docker-compose -f docker-compose.prod.yml exec web /bin/bash
    else
        docker-compose exec web /bin/bash
    fi
}

# Function to check container status
check_status() {
    if [ "$1" == "prod" ]; then
        docker-compose -f docker-compose.prod.yml ps
    else
        docker-compose ps
    fi
}

# Check if a command was provided
if [ $# -eq 0 ]; then
    show_usage
    exit 0
fi

# Process commands
case "$1" in
    dev)
        start_dev
        ;;
    prod)
        start_prod
        ;;
    stop)
        stop_containers
        ;;
    restart)
        restart_containers "$2"
        ;;
    logs)
        view_logs "$2"
        ;;
    clean)
        clean_up
        ;;
    shell)
        open_shell "$2"
        ;;
    status)
        check_status "$2"
        ;;
    help)
        show_usage
        ;;
    *)
        print_message "$RED" "Unknown command: $1"
        show_usage
        exit 1
        ;;
esac

exit 0
