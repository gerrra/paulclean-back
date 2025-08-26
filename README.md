# Cleaning Service API

A comprehensive FastAPI backend for managing cleaning services, including order processing, pricing calculations, and business logic implementation.

## Features

- **Authentication & Authorization**: JWT-based authentication for clients and admins
- **Order Management**: Complete order lifecycle with status tracking
- **Pricing Engine**: Sophisticated pricing calculations with surcharges
- **Scheduling System**: Timeslot management with conflict detection
- **Service Management**: Configurable services with pricing parameters
- **Cleaner Management**: Staff assignment and availability tracking
- **Business Rules**: Strict validation of business logic and constraints

## Architecture

- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: SQL toolkit and ORM
- **Pydantic**: Data validation using Python type annotations
- **SQLite**: Lightweight database (easily switchable to PostgreSQL)
- **JWT**: Secure authentication with JSON Web Tokens

## Business Logic

### Pricing Calculations

The system implements complex pricing rules for different service types:

- **Couch Cleaning**: Base price + cushion/pillow counts + surcharges
- **Rug Cleaning**: Area-based pricing (width × length × rate)
- **Window Cleaning**: Per-window pricing
- **Surcharges**: Base cleaning (38%), pet hair (15%), urine stains (5%), accelerated drying ($45)

### Duration Mapping

Service duration is automatically calculated based on total price:
- $120-200: 2 hours
- $200-300: 3 hours
- $300-400: 4 hours
- $400-500: 5 hours
- $500+: 6 hours

### Scheduling Rules

- Working hours: 10:00 AM - 7:00 PM
- Timeslot increments: 30 minutes
- Conflict detection prevents double-booking
- Future date validation only

## 🚀 Quick Start

### Option 1: Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd cleaning-service-api
   ```

2. **Make scripts executable**
   ```bash
   chmod +x scripts/*.sh
   ```

3. **Start the application**
   ```bash
   ./scripts/start.sh
   ```

   This script will:
   - Check Docker and Docker Compose
   - Generate SSL certificates
   - Create environment file
   - Start all services
   - Run database migrations
   - Initialize sample data

4. **Access the application**
   - API: https://localhost
   - Documentation: https://localhost/docs
   - Health Check: https://localhost/health

### Option 2: Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd cleaning-service-api
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**
   ```bash
   python scripts/init_db.py
   ```

6. **Run the application**
   ```bash
   python run.py
   ```

### Option 3: Production Deployment

1. **Set up production environment**
   ```bash
   cp env.example .env.prod
   # Edit .env.prod with production values
   ```

2. **Start production services**
   ```bash
   docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
   ```

3. **Run migrations**
   ```bash
   docker-compose -f docker-compose.prod.yml exec api alembic upgrade head
   ```

## API Documentation

Once running, access the interactive API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🗄️ Database Setup

### Development (SQLite)
The application automatically creates SQLite database tables on startup.

### Production (PostgreSQL)
The Docker setup includes PostgreSQL with automatic initialization.

### Database Migrations

**Using Alembic (recommended):**
```bash
# Check migration status
alembic current

# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# View migration history
alembic history --verbose
```

**Using Docker:**
```bash
# Run migrations in container
docker-compose exec api alembic upgrade head

# Check status
docker-compose exec api alembic current
```

**Using the migration script:**
```bash
./scripts/migrate.sh
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_pricing.py

# Run tests with verbose output
pytest -v
```

## API Endpoints

### Authentication & Security
- `POST /api/register` - Client registration with email verification
- `POST /api/login` - Client authentication with 2FA support
- `POST /api/admin/login` - Admin authentication
- `POST /api/refresh` - Refresh access token
- `POST /api/logout` - Logout and revoke tokens
- `POST /api/verify-email` - Verify email address
- `POST /api/setup-2fa` - Initialize 2FA setup
- `POST /api/enable-2fa` - Enable 2FA after verification
- `POST /api/disable-2fa` - Disable 2FA protection
- `POST /api/password-reset` - Request password reset
- `POST /api/password-reset/confirm` - Confirm password reset

### Client Operations
- `GET /api/profile` - Get client profile
- `PUT /api/profile` - Update client profile

### Order Management
- `POST /api/orders` - Create new order
- `GET /api/orders/{order_id}` - Get order details
- `GET /api/orders/slots` - Get available timeslots
- `POST /api/orders/calc` - Calculate order price/duration

### Admin Operations
- `GET /api/admin/orders` - List all orders
- `PUT /api/admin/orders/{order_id}/status` - Update order status
- `PUT /api/admin/orders/{order_id}/cleaner` - Assign cleaner
- `GET /api/admin/services` - List services
- `POST /api/admin/services` - Create service
- `GET /api/admin/cleaners` - List cleaners
- `POST /api/admin/cleaners` - Create cleaner

## ⚙️ Configuration

### Environment Variables

Key configuration options in `.env`:

```env
# Database
DATABASE_URL=sqlite:///./cleaning_service.db  # Development
# DATABASE_URL=postgresql://user:pass@localhost/cleaning_service  # Production

# JWT
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Working Hours
WORKING_HOURS_START=10:00
WORKING_HOURS_END=19:00
SLOT_DURATION_MINUTES=30

# Google Calendar (optional)
GOOGLE_CREDENTIALS_FILE=path/to/credentials.json
GOOGLE_TOKEN_FILE=path/to/token.json

# Email (optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Redis (for Celery)
REDIS_URL=redis://localhost:6379

# Production (for docker-compose.prod.yml)
POSTGRES_PASSWORD=your-secure-password
REDIS_PASSWORD=your-redis-password
GRAFANA_PASSWORD=your-grafana-password
```

### Docker Configuration

**Development:**
- `docker-compose.yml` - Basic setup with PostgreSQL, Redis, and FastAPI
- `Dockerfile` - Development-optimized container

**Production:**
- `docker-compose.prod.yml` - Full production stack with monitoring
- `Dockerfile.prod` - Multi-stage production build
- Includes Prometheus, Grafana, Celery workers, and Nginx

## 🔒 Security Features

### **Multi-Factor Authentication (2FA)**
- **TOTP-based 2FA** using authenticator apps (Google Authenticator, Authy)
- **QR code generation** for easy setup
- **Time-based validation** with configurable time windows
- **Automatic 2FA enforcement** for all authenticated endpoints

### **Token Security**
- **Short-lived access tokens** (15 minutes) for reduced attack surface
- **Refresh token rotation** with automatic revocation
- **Secure token storage** in database with expiration tracking
- **Logout endpoint** for immediate token invalidation

### **Email Verification**
- **Mandatory email verification** for new accounts
- **Secure verification tokens** with 24-hour expiration
- **Professional HTML email templates** with branding
- **Anti-enumeration protection** in password reset

### **Rate Limiting & Protection**
- **IP-based rate limiting** for all authentication endpoints
- **Account lockout** after 5 failed login attempts (15-minute lockout)
- **Configurable rate limits** (100 requests per 15 minutes)
- **Brute force protection** with progressive delays

### **Password Security**
- **Strong password requirements** (minimum 8 characters)
- **Secure password reset** via time-limited email tokens
- **Bcrypt hashing** with industry-standard salt rounds
- **Password strength validation** in registration

## Business Rules Implementation

### Order Validation
- Future dates only
- Working hours compliance
- Timeslot availability
- Service parameter validation

### Pricing Validation
- Positive numbers only
- Surcharge percentage limits
- Cost-to-duration mapping

### Status Transitions
- Pending Confirmation → Confirmed/Cancelled
- Confirmed → Completed/Cancelled
- Completed/Cancelled → No further transitions

## Extending the System

### Adding New Services
1. Create service via admin API
2. Configure pricing parameters
3. Set category and surcharges
4. Publish when ready

### Custom Pricing Rules
Modify `PricingService.calculate_service_cost()` to add new calculation logic.

### Additional Validations
Extend Pydantic models with custom validators for new business rules.

## 🐳 Docker & Deployment

### Development Environment

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild and start
docker-compose up --build -d
```

### Production Environment

```bash
# Start production stack
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d

# Scale workers
docker-compose -f docker-compose.prod.yml up -d --scale celery_worker=3

# View production logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Health Checks

All services include health checks:
- **FastAPI**: `/health` endpoint
- **PostgreSQL**: `pg_isready` command
- **Redis**: `ping` command
- **Nginx**: Service dependency checks

### Monitoring Stack

Production setup includes:
- **Prometheus**: Metrics collection
- **Grafana**: Visualization dashboards
- **Nginx**: Reverse proxy with rate limiting
- **Celery**: Background task processing

## 🚀 Production Considerations

1. **Security**
   - Change default secret key
   - Use HTTPS with proper SSL certificates
   - Implement rate limiting via Nginx
   - Add input sanitization
   - Use production environment variables

2. **Performance**
   - Database connection pooling
   - Redis caching layer
   - Celery background task processing
   - API response optimization
   - Nginx load balancing

3. **Monitoring**
   - Prometheus metrics collection
   - Grafana dashboards
   - Health checks for all services
   - Structured logging
   - Error tracking and alerting

4. **Deployment**
   - Multi-stage Docker builds
   - Environment-specific configurations
   - Database backups and migrations
   - CI/CD pipeline integration
   - Container orchestration (Kubernetes ready)

## 🔧 Troubleshooting

### Common Issues

**Database Connection Errors:**
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# View database logs
docker-compose logs postgres

# Test connection
docker-compose exec postgres pg_isready -U cleaning_user
```

**Migration Issues:**
```bash
# Check migration status
alembic current

# Reset migrations (development only)
alembic downgrade base
alembic upgrade head

# View migration history
alembic history --verbose
```

**SSL Certificate Issues:**
```bash
# Regenerate SSL certificates
./scripts/generate_ssl.sh

# Check certificate validity
openssl x509 -in nginx/ssl/cert.pem -text -noout
```

**Service Health Checks:**
```bash
# Check all service health
docker-compose ps

# View health check logs
docker-compose logs api | grep health

# Manual health check
curl -f http://localhost:8000/health
```

### Performance Tuning

**Database Optimization:**
```bash
# Increase PostgreSQL connections
# Edit docker-compose.yml: POSTGRES_MAX_CONNECTIONS=200

# Add database indexes
# Use Alembic to create custom migrations
```

**API Optimization:**
```bash
# Scale workers
docker-compose up -d --scale api=3

# Enable Redis caching
# Set REDIS_CACHE_ENABLED=true in .env
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Implement changes with tests
4. Submit pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions and support:
- Create an issue in the repository
- Contact: support@cleaningservice.com
- Documentation: http://localhost:8000/docs (when running)
