# Radar - Enterprise Competitor Intelligence Platform

Enterprise-grade competitor monitoring application that delivers automated quarterly PDF intelligence reports via email, plus an on-demand executive web dashboard.

**For CEOs and CFOs only.** This is a production-ready, Fortune-500-level intelligence platform.

## Features

- **Authentication & Authorization**
  - Role-based access control (CEO, CFO, Admin)
  - Multi-factor authentication (TOTP with QR codes)
  - OAuth integration (Google, Microsoft)
  - Secure password management

- **Company & Competitor Management**
  - Company onboarding with automatic metadata extraction
  - Intelligent competitor discovery (5 suggested competitors)
  - Competitor approval workflow

- **Intelligence Collection**
  - Financial data (Alpha Vantage, Finnhub)
  - Funding & M&A (Crunchbase)
  - Patents & IP (USPTO, PatentsView)
  - News & media (NewsAPI, The News API)
  - Web traffic (SimilarWeb)
  - Social signals (X/Twitter API)

- **Analysis & Insights**
  - Financial ratio analysis
  - Competitive positioning and threat scoring
  - Sentiment analysis (news and social)
  - Startup discovery and scoring
  - Data-grounded SWOT analysis

- **Executive Reports**
  - 10-15 page board-ready PDF reports
  - Executive summary with actionable insights
  - Threat scores, opportunities, and recommendations
  - Professional charts and visualizations
  - Role-specific tone (CEO vs CFO)

- **Automated Delivery**
  - Quarterly automated report generation
  - Secure email delivery via SendGrid
  - Real-time alerts (M&A, funding, IP spikes)

- **Executive Dashboard**
  - Historical reports access
  - On-demand views
  - Forecasting capabilities
  - Mobile responsive

## Architecture

The system follows a layered architecture with clear separation of concerns:

- **Backend**: Flask application with factory pattern
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache**: Redis for caching and rate limiting
- **Background Tasks**: Celery with Redis broker
- **Report Generation**: WeasyPrint for PDF generation
- **Email**: SendGrid for email delivery

## Technology Stack

- Python 3.11+
- Flask (web framework)
- SQLAlchemy (ORM)
- PostgreSQL (database)
- Redis (caching and rate limiting)
- Celery (background tasks)
- WeasyPrint (PDF generation)
- SendGrid (email delivery)
- Various intelligence APIs (Crunchbase, Alpha Vantage, etc.)

## Installation

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker and Docker Compose (optional)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd radar
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
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**
   ```bash
   flask db upgrade
   # Or run migrations manually
   alembic upgrade head
   ```

6. **Run the application**
   ```bash
   flask run
   ```

### Docker Setup

```bash
docker-compose up -d
```

This will start:
- Web application (Flask)
- PostgreSQL database
- Redis cache
- Celery worker
- Celery beat scheduler

## Configuration

### Environment Variables

See `.env.example` for all required environment variables. Key variables:

- `SECRET_KEY`: Flask secret key (generate with `python -c "import secrets; print(secrets.token_hex(32))"`)
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- API keys for intelligence sources (Alpha Vantage, Crunchbase, etc.)
- OAuth credentials (Google, Microsoft)
- SendGrid API key for email delivery

### Security Configuration

- **Encryption**: Fernet encryption for sensitive data (API keys, MFA secrets)
- **Rate Limiting**: Redis-based rate limiting (configurable per endpoint)
- **CSRF Protection**: Flask-WTF CSRF protection enabled
- **Input Sanitization**: Bleach for XSS prevention
- **Password Hashing**: bcrypt with cost factor 12

## Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Running Tests

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run security scanning
bandit -r app
```

## Development

### Project Structure

```
radar/
├── app/
│   ├── auth/          # Authentication and authorization
│   ├── companies/     # Company and competitor management
│   ├── intelligence/  # Intelligence collection and analysis
│   ├── reports/       # Report generation
│   ├── dashboard/     # Executive dashboard
│   ├── scheduling/    # Background tasks
│   ├── email/         # Email delivery
│   └── utils/         # Utility functions
├── migrations/        # Alembic migrations
├── tests/            # Test suite
├── storage/          # Generated reports storage
└── logs/             # Application logs
```

### Code Quality

- **Linting**: `flake8` and `black` for code formatting
- **Type Checking**: `mypy` for static type analysis
- **Security**: `bandit` for security vulnerability scanning

```bash
# Format code
black app/

# Lint code
flake8 app/

# Type check
mypy app/

# Security scan
bandit -r app
```

## API Documentation

### Authentication Endpoints

- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Authenticate user
- `POST /api/auth/logout` - Logout user
- `POST /api/auth/refresh` - Refresh access token
- `POST /api/auth/mfa/setup` - Setup MFA
- `POST /api/auth/mfa/verify` - Verify MFA code
- `GET /api/auth/me` - Get current user

### Company Endpoints

- `POST /api/companies` - Create company
- `GET /api/companies` - Get all companies
- `POST /api/companies/<id>/competitors/discover` - Discover competitors
- `GET /api/companies/<id>/competitors` - Get competitors
- `POST /api/companies/competitors/<id>/approve` - Approve competitor

### Report Endpoints

- `POST /api/reports/generate` - Generate on-demand report
- `GET /api/reports/<id>` - Get report metadata
- `GET /api/reports/<id>/download` - Download report PDF

## Deployment

### Production Considerations

1. **Security**
   - Use strong, randomly generated secrets
   - Enable HTTPS (TLS/SSL)
   - Configure proper CORS origins
   - Set up rate limiting
   - Regular security audits

2. **Database**
   - Use connection pooling
   - Set up database backups
   - Monitor query performance
   - Use read replicas if needed

3. **Caching**
   - Configure Redis persistence
   - Set appropriate TTLs for cached data
   - Monitor cache hit rates

4. **Background Tasks**
   - Configure Celery workers with appropriate concurrency
   - Set up monitoring for task failures
   - Implement task retry logic

5. **Monitoring**
   - Set up Sentry for error tracking
   - Configure Prometheus metrics
   - Set up log aggregation
   - Monitor API rate limits

### Deployment Platforms

The application is designed to be cloud-agnostic and can be deployed on:

- AWS (EC2/ECS/EKS)
- Azure
- Google Cloud Platform
- Docker (Kubernetes)

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check DATABASE_URL format
   - Verify PostgreSQL is running
   - Check network connectivity

2. **Redis Connection Errors**
   - Verify Redis is running
   - Check REDIS_URL format
   - Check Redis configuration

3. **API Rate Limits**
   - Check rate limit configuration
   - Monitor Redis for rate limit keys
   - Adjust limits as needed

4. **Report Generation Failures**
   - Check WeasyPrint dependencies
   - Verify storage directory permissions
   - Check disk space

## License

Proprietary - All rights reserved

## Support

For support, contact the development team or refer to internal documentation.

## Security Notes

- All API keys and secrets are encrypted at rest using Fernet
- MFA secrets are encrypted before storage
- Passwords are hashed using bcrypt
- All user inputs are sanitized to prevent XSS
- CSRF protection is enabled for all POST requests
- Rate limiting is enforced on authentication endpoints
- JWT tokens have configurable expiration times
- Refresh tokens are stored securely and rotated

## Contributing

This is an enterprise application. All contributions must:

1. Follow the code style guidelines (black, flake8)
2. Include comprehensive tests
3. Pass security scanning (bandit)
4. Be reviewed by the development team
5. Meet production-ready standards
