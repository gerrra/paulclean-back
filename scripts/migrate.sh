#!/bin/bash

# Database migration script for Cleaning Service API
# This script runs Alembic migrations

set -e

echo "🗄️  Running database migrations..."

# Check if we're running in Docker
if [ -f /.dockerenv ]; then
    echo "🐳 Running in Docker container..."
    cd /app
else
    echo "💻 Running locally..."
fi

# Check if alembic is installed
if ! command -v alembic &> /dev/null; then
    echo "❌ Alembic is not installed. Installing..."
    pip install alembic
fi

# Check if we have a database connection
echo "🔍 Checking database connection..."

# Run migrations
echo "📊 Running migrations..."
alembic upgrade head

echo "✅ Database migrations completed successfully!"
echo ""
echo "📋 Migration status:"
alembic current
echo ""
echo "📝 Migration history:"
alembic history --verbose
