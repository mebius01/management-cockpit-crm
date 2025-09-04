# Multi-stage Dockerfile for Django Entity Management CRM
# Supports: local, test, staging, production environments

# Base stage with common dependencies
FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
  PYTHONDONTWRITEBYTECODE=1 \
  PIP_NO_CACHE_DIR=1 \
  PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
  build-essential \
  libpq-dev \
  && rm -rf /var/lib/apt/lists/*

# Create app user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set work directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY pyproject.toml ./
RUN pip install --upgrade pip && \
  pip install -e .

# Development stage
FROM base AS development

# Install development dependencies
RUN pip install -e ".[dev]"

# Copy application code
COPY . .

# Change ownership to app user
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Default command for development
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# Test stage
FROM base AS test

# Install test dependencies
RUN pip install -e ".[dev]"

# Copy application code
COPY . .

# Change ownership to app user
RUN chown -R appuser:appuser /app
USER appuser

# Run tests
CMD ["python", "-m", "pytest", "-v", "--tb=short"]

# Staging stage
FROM base AS staging

# Install production dependencies only
RUN pip install -e .

# Copy application code
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput --settings=app.settings

# Change ownership to app user
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health/', timeout=10)"

# Run with gunicorn for staging
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120", "app.wsgi:application"]

# Production stage
FROM base AS production

# Install production dependencies only
RUN pip install -e .

# Copy application code
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput --settings=app.settings

# Change ownership to app user
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health/', timeout=10)"

# Run with gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "--max-requests", "1000", "--max-requests-jitter", "100", "app.wsgi:application"]
