# Django CRM Project

Django REST API project with PostgreSQL database and environment-based configuration.

## Development Setup

### 1. Create Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Linux/macOS:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

Create `.env` file in the project root:

Edit `.env` with your configuration:

```env
# Base
DJANGO_DEBUG=<True|False>
DJANGO_LANGUAGE_CODE=<your-language-code>
DJANGO_TIME_ZONE=<your-time-zone>
DJANGO_ALLOWED_HOSTS=<your-allowed-hosts>
DJANGO_CSRF_TRUSTED_ORIGINS=<your-csrf-trusted-origins>
DRF_PAGE_SIZE=<your-drf-page-size>

# Security
DJANGO_SECRET_KEY=<your-secret-key>
DJANGO_SECURE=<True|False>
DJANGO_HSTS_SECONDS=<your-hsts-seconds>

# Postgres
POSTGRES_HOST=<your-postgres-host>
POSTGRES_DB=<your-postgres-db>
POSTGRES_PORT=<your-postgres-port>
POSTGRES_USER=<your-postgres-user>
POSTGRES_PASSWORD=<your-postgres-password>
DJANGO_DB_CONN_MAX_AGE=<your-db-conn-max-age>
```

### 4. Start Database with Docker Compose

The project includes a `docker-compose.yml` file to run PostgreSQL database:

```bash
# Start PostgreSQL database
docker-compose up -d

# Check if database is running
docker-compose ps

# View database logs (optional)
docker-compose logs crm-pg

# Stop database (when needed)
docker-compose down
```

The database will be available on the port specified in your `.env` file (`POSTGRES_PORT`).

### 5. Create Migrations

```bash
python manage.py migrate
```

The application will be available at: http://127.0.0.1:8000/

### 6. Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

## Project Structure

```
├── app/                    # Django project settings
│   ├── settings.py        # Main settings with environment variables
│   ├── urls.py           # URL configuration
│   └── ...
├── entity/               # Main application
│   ├── models.py        # Database models
│   ├── views.py         # API views
│   └── ...
├── requirements.txt      # Python dependencies
├── .env.example         # Environment variables template
└── manage.py           # Django management script
```

## API Documentation

- Admin panel: http://127.0.0.1:8000/admin/

## Technologies Used

- **Django 5.2.5** - Web framework
- **Django REST Framework** - API framework
- **PostgreSQL** - Primary database
- **django-environ** - Environment variable management

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create migrations
python manage.py makemigrations

# Run development server
python manage.py runserver

# Run tests
python manage.py test

# Create superuser
python manage.py createsuperuser