#!/bin/bash

# Comprehensive startup script for Cleaning Service API
# This script sets up and starts the entire application

set -e

echo "🚀 Starting Cleaning Service API..."
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
check_docker() {
    print_status "Checking Docker..."
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    print_success "Docker is running"
}

# Check if Docker Compose is available
check_docker_compose() {
    print_status "Checking Docker Compose..."
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install it and try again."
        exit 1
    fi
    print_success "Docker Compose is available"
}

# Generate SSL certificates if they don't exist
generate_ssl() {
    if [ ! -f "nginx/ssl/cert.pem" ] || [ ! -f "nginx/ssl/key.pem" ]; then
        print_status "Generating SSL certificates..."
        chmod +x scripts/generate_ssl.sh
        ./scripts/generate_ssl.sh
        print_success "SSL certificates generated"
    else
        print_success "SSL certificates already exist"
    fi
}

# Create environment file if it doesn't exist
create_env() {
    if [ ! -f ".env" ]; then
        print_status "Creating .env file from template..."
        cp env.example .env
        print_warning "Please edit .env file with your configuration before starting"
        print_success ".env file created"
    else
        print_success ".env file already exists"
    fi
}

# Start the application
start_app() {
    print_status "Starting application with Docker Compose..."
    
    # Build and start services
    docker-compose up --build -d
    
    print_success "Application started successfully!"
    echo ""
    echo "🌐 Services:"
    echo "   - FastAPI: http://localhost:8000"
    echo "   - HTTPS: https://localhost"
    echo "   - API Docs: https://localhost/docs"
    echo "   - ReDoc: https://localhost/redoc"
    echo "   - Health: https://localhost/health"
    echo ""
    echo "🗄️  Database:"
    echo "   - PostgreSQL: localhost:5432"
    echo "   - Redis: localhost:6379"
    echo ""
    echo "📊 Monitor logs: docker-compose logs -f"
    echo "🛑 Stop services: docker-compose down"
}

# Wait for services to be ready
wait_for_services() {
    print_status "Waiting for services to be ready..."
    
    # Wait for PostgreSQL
    print_status "Waiting for PostgreSQL..."
    until docker-compose exec -T postgres pg_isready -U cleaning_user -d cleaning_service > /dev/null 2>&1; do
        sleep 2
    done
    print_success "PostgreSQL is ready"
    
    # Wait for Redis
    print_status "Waiting for Redis..."
    until docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; do
        sleep 2
    done
    print_success "Redis is ready"
    
    # Wait for FastAPI
    print_status "Waiting for FastAPI..."
    until curl -f http://localhost:8000/health > /dev/null 2>&1; do
        sleep 2
    done
    print_success "FastAPI is ready"
}

# Run database migrations
run_migrations() {
    print_status "Running database migrations..."
    chmod +x scripts/migrate.sh
    docker-compose exec api ./scripts/migrate.sh
    print_success "Database migrations completed"
}

# Initialize database with sample data
init_database() {
    print_status "Initializing database with sample data..."
    docker-compose exec api python scripts/init_db.py
    print_success "Database initialized with sample data"
}

# Main execution
main() {
    echo ""
    print_status "Starting Cleaning Service API setup..."
    
    # Pre-flight checks
    check_docker
    check_docker_compose
    
    # Setup
    create_env
    generate_ssl
    
    # Start application
    start_app
    
    # Wait for services
    wait_for_services
    
    # Setup database
    run_migrations
    init_database
    
    echo ""
    print_success "🎉 Cleaning Service API is ready!"
    echo ""
    echo "🔑 Default credentials:"
    echo "   - Admin: admin / admin123"
    echo "   - Client: john.doe@example.com (no password required for demo)"
    echo ""
    echo "📚 Next steps:"
    echo "   1. Visit https://localhost/docs to explore the API"
    echo "   2. Test the endpoints with the provided credentials"
    echo "   3. Check logs: docker-compose logs -f"
    echo ""
}

# Run main function
main "$@"
