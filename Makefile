# Makefile for Cleaning Service API
# Provides common commands for development and deployment

.PHONY: help install dev prod test clean migrate init-db logs ssl

# Default target
help:
	@echo "🚀 Cleaning Service API - Available Commands"
	@echo "============================================="
	@echo ""
	@echo "Development:"
	@echo "  make install     - Install Python dependencies"
	@echo "  make dev         - Start development environment"
	@echo "  make test        - Run tests"
	@echo "  make clean       - Clean up development files"
	@echo ""
	@echo "Database:"
	@echo "  make migrate     - Run database migrations"
	@echo "  make init-db     - Initialize database with sample data"
	@echo ""
	@echo "Production:"
	@echo "  make prod        - Start production environment"
	@echo "  make logs        - View application logs"
	@echo ""
	@echo "Utilities:"
	@echo "  make ssl         - Generate SSL certificates"
	@echo "  make help        - Show this help message"

# Install Python dependencies
install:
	@echo "📦 Installing Python dependencies..."
	pip install -r requirements.txt

# Start development environment
dev:
	@echo "🐳 Starting development environment..."
	@if [ ! -f ".env" ]; then \
		echo "⚠️  Creating .env file from template..."; \
		cp env.example .env; \
		echo "📝 Please edit .env file with your configuration"; \
	fi
	@if [ ! -f "nginx/ssl/cert.pem" ] || [ ! -f "nginx/ssl/key.pem" ]; then \
		echo "🔐 Generating SSL certificates..."; \
		chmod +x scripts/generate_ssl.sh; \
		./scripts/generate_ssl.sh; \
	fi
	@echo "🚀 Starting services..."
	docker-compose up --build -d
	@echo "⏳ Waiting for services to be ready..."
	@until curl -f http://localhost:8000/health > /dev/null 2>&1; do \
		sleep 2; \
	done
	@echo "✅ Development environment is ready!"
	@echo "🌐 API: http://localhost:8000"
	@echo "📚 Docs: http://localhost:8000/docs"
	@echo "🔒 HTTPS: https://localhost"

# Start production environment
prod:
	@echo "🚀 Starting production environment..."
	@if [ ! -f ".env.prod" ]; then \
		echo "⚠️  Please create .env.prod file with production values"; \
		exit 1; \
	fi
	docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
	@echo "✅ Production environment started!"

# Run tests
test:
	@echo "🧪 Running tests..."
	pytest tests/ -v --cov=app

# Clean up development files
clean:
	@echo "🧹 Cleaning up development files..."
	docker-compose down -v
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf cleaning_service.db
	@echo "✅ Cleanup completed!"

# Run database migrations
migrate:
	@echo "🗄️  Running database migrations..."
	@if [ -f /.dockerenv ]; then \
		alembic upgrade head; \
	else \
		docker-compose exec api alembic upgrade head; \
	fi

# Initialize database with sample data
init-db:
	@echo "📊 Initializing database with sample data..."
	@if [ -f /.dockerenv ]; then \
		python scripts/init_db.py; \
	else \
		docker-compose exec api python scripts/init_db.py; \
	fi

# View application logs
logs:
	@echo "📋 Viewing application logs..."
	docker-compose logs -f

# Generate SSL certificates
ssl:
	@echo "🔐 Generating SSL certificates..."
	chmod +x scripts/generate_ssl.sh
	./scripts/generate_ssl.sh

# Database operations
db-reset: clean
	@echo "🔄 Resetting database..."
	docker-compose up -d postgres
	@until docker-compose exec -T postgres pg_isready -U cleaning_user > /dev/null 2>&1; do \
		sleep 2; \
	done
	make migrate
	make init-db
	@echo "✅ Database reset completed!"

# Health check
health:
	@echo "🏥 Checking service health..."
	@curl -f http://localhost:8000/health || echo "❌ Health check failed"

# Stop all services
stop:
	@echo "🛑 Stopping all services..."
	docker-compose down
	@echo "✅ Services stopped!"

# Restart services
restart: stop dev

# Show service status
status:
	@echo "📊 Service status:"
	docker-compose ps

# Build images
build:
	@echo "🔨 Building Docker images..."
	docker-compose build --no-cache

# Production build
build-prod:
	@echo "🔨 Building production Docker images..."
	docker-compose -f docker-compose.prod.yml build --no-cache

# Backup database
backup:
	@echo "💾 Creating database backup..."
	@mkdir -p backups
	docker-compose exec postgres pg_dump -U cleaning_user cleaning_service > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Backup created in backups/ directory"

# Restore database
restore:
	@echo "📥 Restoring database from backup..."
	@if [ -z "$(FILE)" ]; then \
		echo "❌ Please specify backup file: make restore FILE=backups/backup_20240101_120000.sql"; \
		exit 1; \
	fi
	docker-compose exec -T postgres psql -U cleaning_user -d cleaning_service < $(FILE)
	@echo "✅ Database restored from $(FILE)"
