# Management Cockpit CRM (SCD2 Core)

This project provides a robust foundation for a Management Cockpit CRM, built on Django and PostgreSQL. Its core feature is the implementation of **Slowly Changing Dimensions (SCD) Type 2** versioning directly within the main data tables, enabling full historical tracking of all data changes.

## Key Features

- **SCD Type 2 Versioning**: All entities and their details are versioned in-place using `valid_from`, `valid_to`, and `is_current` fields.
- **Temporal Queries**: Full support for "as-of" point-in-time queries and calculating differences between two time points.
- **Idempotent Operations**: Services are designed to be idempotent, preventing duplicate data entries on replay using hashdiff-based change detection.
- **Database-First Constraints**: Leverages PostgreSQL's advanced features like `Exclusion Constraints` to guarantee data integrity at the database level.
- **Service-Oriented Architecture**: Business logic is encapsulated in a dedicated service layer, separating it from the API views.
- **Comprehensive Audit Trail**: Complete logging of all changes with actor, timestamp, and before/after data.
- **DRF Token Authentication**: Secure API access using Django REST Framework token authentication with user context and audit logging.

## Getting Started

Follow these steps to set up and run the project locally. The project supports both local development and Docker-based development.

### Prerequisites

- **Python 3.10+** (3.13 recommended)
- **Docker & Docker Compose** (for database or full containerized setup)
- **Git** (for cloning the repository)

### Development Options

This project offers two development approaches:

1. **Local Development** - Python virtual environment + Docker database
2. **Full Docker** - Everything running in containers

Choose the approach that best fits your workflow.

## Option 1: Local Development (Recommended)

### 1. Clone & Configure

Clone the repository and navigate into the project directory.

```bash
git clone <your-repository-url>
cd management-cockpit-crm
```

### 2. Understanding the Makefile

This project includes a comprehensive Makefile that simplifies development tasks. Before setting up the environment, let's explore the available commands.

#### View all available commands:

```bash
make help
```

This will display all available commands organized into two categories:
- **Development commands (local)**: For local development with virtual environment
- **Docker commands**: For containerized development

#### Key Makefile features:

- **Simplified workflow**: Complex commands are wrapped in simple `make` targets
- **Consistent interface**: Same commands work across different environments
- **Error handling**: Built-in checks and helpful error messages
- **Documentation**: Each command is self-documenting with descriptions

#### Example output of `make help`:

```
Development commands (local):
  make dev-venv        - Create virtual environment
  make dev-setup       - Setup development environment
  make dev-run         - Run development server
  make dev-migrate     - Run migrations locally
  make dev-fixtures    - Load fixtures locally
  make dev-shell       - Open Django shell locally
  make dev-test        - Run tests locally

Docker commands:
  make up              - Start both database and application
  make up-dev          - Start development with hot reload
  make up-db           - Start only database
  make up-app          - Start only application
  make down            - Stop all services
  make logs            - Show application logs
  make migrate         - Run database migrations (Docker)
  make fixtures        - Load fixtures (Docker)
  make clean           - Clean up containers and volumes
```


### 3. Set Up Virtual Environment

Create and activate a Python virtual environment using the provided Makefile commands.

#### What happens during environment setup:

1. **Virtual Environment Creation**: The `make dev-venv` command runs `python -m venv .venv` which:
   - Uses Python 3.13 interpreter to create a virtual environment
   - Creates a `.venv` directory with isolated Python installation
   - Installs pip and setuptools in the virtual environment
   - Sets up proper Python path configuration
2. **Isolation**: This ensures project dependencies don't conflict with your system Python or other projects
3. **Activation**: The `source .venv/bin/activate` command switches your shell to use the virtual environment's Python interpreter and packages

#### Manual environment creation (alternative to Makefile):

If you prefer to create the environment manually:

```bash
# Create virtual environment with specific Python version
python -m venv .venv

# This command:
# - python3.13: Uses Python 3.13 interpreter
# - -m venv: Runs the venv module
# - .venv: Creates environment in .venv directory
```

#### Step-by-step process:

```bash
# Create virtual environment with Python 3.13
make dev-venv

# Activate the virtual environment (required for each new terminal session)
source .venv/bin/activate

# Verify activation (you should see (.venv) in your prompt)
which python
# Should show: /path/to/project/.venv/bin/python
```

**Important**: You must activate the virtual environment in each new terminal session before running development commands.

### 4. Configure Environment Variables

Create a `.env` file by copying the example file.

```bash
cp env.example .env
```

Edit the `.env` file with your local settings. The default values work with the Docker Compose setup.

### 5. Start the Database

Start only the PostgreSQL database using Docker Compose.

```bash
# Start database only
make up-db

# Or manually
docker compose -f docker-compose.pg.yml up -d
```

### 6. Install Dependencies

Install the required Python packages using the Makefile.

```bash
make dev-setup
```

This installs both main dependencies and development tools from `pyproject.toml`.

### 7. Run Database Migrations

Apply the database schema migrations.

```bash
make dev-migrate
```

### 8. Load Initial Data (Fixtures)

Load the sample data including entity types, detail types, sample entities, and test users.

```bash
make dev-fixtures
```

### 9. Create a Superuser (Optional)

To access the Django admin panel, create a superuser.

```bash
python manage.py createsuperuser
```

### 10. Run the Development Server

Start the Django development server.

```bash
make dev-run
```

The application will be available at `http://127.0.0.1:8000/`.

## Option 2: Full Docker Development

### 1. Clone & Configure

```bash
git clone <your-repository-url>
cd management-cockpit-crm
```

### 2. Configure Environment Variables

```bash
cp env.example .env
```

### 3. Start All Services

Start both database and application in Docker containers.

```bash
# Start everything
make up

# Or for development with hot reload
make up-dev
```

### 4. Run Migrations & Load Data

```bash
# Run migrations
make migrate

# Load fixtures
make fixtures
```

### 5. Access the Application

The application will be available at `http://127.0.0.1:8000/`.

## Available Makefile Commands

### Development Commands (Local)
- `make dev-venv` - Create virtual environment
- `make dev-setup` - Install dependencies
- `make dev-run` - Run development server
- `make dev-migrate` - Run migrations
- `make dev-fixtures` - Load sample data
- `make dev-shell` - Open Django shell
- `make dev-test` - Run tests

### Docker Commands
- `make up` - Start both database and application
- `make up-dev` - Start development with hot reload
- `make up-db` - Start only database
- `make up-app` - Start only application
- `make down` - Stop all services
- `make logs` - Show application logs
- `make migrate` - Run migrations (Docker)
- `make fixtures` - Load fixtures (Docker)
- `make clean` - Clean up containers and volumes


## API Usage & Postman

The API provides full programmatic access to the CRM's features.

### Authentication

All write operations (POST, PATCH, PUT, DELETE) require DRF token authentication. Read operations (GET) are public. Test users are created by the fixtures (`005_users.json`):
- **Username**: `user_1`, **Password**: `1234`
- **Username**: `user_2`, **Password**: `1234`

There are three ways to obtain an authentication token:

**1. Using `curl` (API Request)**
```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/token \
     -H "Content-Type: application/json" \
     -d '{"username": "user_1", "password": "1234"}'
```

**2. Using Postman (API Request)**
1.  Create a new `POST` request.
2.  Set the URL to `{{baseUrl}}/api/v1/auth/token`.
3.  Go to the **Body** tab, select **raw**, and choose **JSON**.
4.  Enter the following in the text area:
    ```json
    {
        "username": "user_1",
        "password": "1234"
    }
    ```
5.  Click **Send**. The token will be in the response body.

**3. Using a Management Command (CLI)**

For development purposes, you can generate a token directly from the command line. If a token already exists for the user, this command will display the existing token.

```bash
# Generate a token for user_1
python manage.py drf_create_token user_1
```

Include the received token in the `Authorization` header for subsequent requests:
`Authorization: Token your_auth_token_here`

### Postman Collection

A Postman collection is provided in the root of this repository: `Management Cockpit CRM.postman_collection.json`.

To use it:
1.  Open Postman.
2.  Click **Import** and select the JSON file.
3.  The collection includes pre-configured requests for all major API endpoints.
4.  You may need to configure the `{{baseUrl}}` variable to `http://127.0.0.1:8000/api/v1`.

### API Endpoint Examples

- **Authentication**: `POST /api/v1/auth/token`
- **Ping**: `GET /ping/` - Application health and system information
- **List Entities**: `GET /api/v1/entities` (with optional filters: `?q=search&type=PERSON`)
- **Get Entity Snapshot**: `GET /api/v1/entities/{entity_uid}`
- **Create Entity**: `POST /api/v1/entities` (requires authentication)
- **Update Entity**: `PATCH /api/v1/entities/{entity_uid}` (requires authentication)
- **As-Of Query**: `GET /api/v1/entities-asof/?as_of=2024-01-15T10:30:00Z`
- **Diff Query**: `GET /api/v1/diff/?from=2024-01-01&to=2024-01-31`

### Ping Endpoint

The `/ping/` endpoint provides comprehensive health monitoring and system information:

**Purpose:**
- Health check for Docker containers and load balancers
- Application status monitoring
- System diagnostics and troubleshooting

**Response Format:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.123456",
  "environment": {
    "debug": false,
    "environment": "production",
    "python_version": "3.13.0",
    "django_version": "5.2.6"
  },
  "database": "connected",
  "features": {
    "scd2_versioning": true,
    "temporal_queries": true,
    "audit_logging": true,
    "token_auth": true
  },
  "endpoints": {
    "api_base": "/api/v1/",
    "admin": "/admin/",
    "ping": "/ping/"
  }
}
```

**Status Codes:**
- `200 OK` - Application is healthy
- `503 Service Unavailable` - Application has issues (database disconnected, etc.)

**Use Cases:**
- Docker health checks
- Load balancer health monitoring
- Application diagnostics
- Environment verification



## Architecture & Design

### Core Principles
- **Single Shared Core**: Central `Entity` model linked via a stable `entity_uid`.
- **SCD2 In-Table Versioning**: Using `valid_from`/`valid_to`/`is_current` with exclusion constraints.
- **Database-First Constraints**: Using PostgreSQL exclusion constraints to prevent data corruption.
- **Idempotency**: Services use hashdiffs to avoid creating duplicate versions.
- **Audit-First Design**: All changes are logged with complete context for compliance and debugging.
- **Service Layer Architecture**: Business logic separated from API views for maintainability.

### Data Model

The core models are `Entity` and `EntityDetail`, both of which are versioned. They are linked to non-versioned `EntityType` and `DetailType` tables.

### Service Layer

Business logic is abstracted into a service layer, ensuring views remain thin. The flow is:
`Views (DRF) → Services → Models (ORM) → Database`

**Key Services:**

**Global Services** (`/services/`):
- **AuditService**: Centralized audit logging for all changes with user context and request tracking
- **HashService**: Computes hashdiffs for idempotent operations and change detection
- **SCD2Service**: Core SCD2 transition logic and version management utilities
- **DateTimeService**: Date/time parsing and validation utilities
- **PaginationService**: Standardized pagination for API responses

**Entity Services** (`/entity/services/`):
- **EntityService**: Handles entity creation, updates, and SCD2 transitions with audit logging
- **AsOfService**: Provides point-in-time query capabilities for temporal data retrieval
- **DiffService**: Calculates differences between time periods for change analysis
- **HistoryService**: Retrieves combined entity and detail history with temporal ordering

## Database & Performance

This section details the SQL-level optimizations and constraints that power the SCD2 implementation.

### Key Constraints

**1. Unique Current Record (Partial Index)**
Ensures only one version of an entity can be marked as `is_current`.
```sql
-- For entities
CONSTRAINT unique_current_entity UNIQUE (entity_uid) WHERE is_current = true;

-- For details
CONSTRAINT unique_current_entity_detail UNIQUE (entity_id, detail_type_id) WHERE is_current = true;
```

**2. Overlap Prevention (Exclusion Constraint)**
Uses a GiST index on a time range to physically prevent any two versions of the same entity from having overlapping validity periods.
```sql
CONSTRAINT exclude_overlapping_entities EXCLUDE USING gist (
  entity_uid WITH =,
  tstzrange(valid_from, COALESCE(valid_to, 'infinity'::timestamptz), '[)') WITH &&
);
```

### Performance & Indexing

The system relies on **covering indexes** to optimize common query patterns.

**1. Current Entity Lookup**
- **Query**: `SELECT * FROM entity WHERE entity_uid = ? AND is_current = true;`
- **Index**: `ent_uid_curr_cov_idx`

**2. As-Of Temporal Query**
- **Query**: `SELECT * FROM entity WHERE valid_from <= ? AND (valid_to > ? OR valid_to IS NULL);`
- **Index**: `ent_valid_from_cov_idx`

**3. Entity Details Lookup**
- **Query**: `SELECT * FROM entity_detail WHERE entity_id = ? AND is_current = true;`
- **Index**: `det_ent_curr_cov_idx`

**4. Hashdiff-based Idempotency**
- **Query**: `SELECT * FROM entity_detail WHERE hashdiff = ?;`
- **Index**: `det_hashdiff_cov_idx`

#### EXPLAIN ANALYZE Example

Querying the state of all entities at a specific point in time demonstrates the use of the temporal index.

```sql
EXPLAIN ANALYZE
SELECT e.entity_uid, e.display_name, e.valid_from
FROM entity e
WHERE e.valid_from <= '2024-01-15T00:00:00Z'
  AND (e.valid_to > '2024-01-15T00:00:00Z' OR e.valid_to IS NULL)
ORDER BY e.entity_uid;

-- Expected Result: Uses an Index Scan on entity_valid_from_covering_idx for high performance.
```

### Troubleshooting

- **Overlapping Periods Error**: This is prevented by the database exclusion constraints, but if it occurs, it indicates a logic error in the application code that tried to create an invalid state.
- **Poor Performance**: Use `EXPLAIN ANALYZE` on your query to ensure the correct covering indexes are being used.
- **Authentication Issues**: Ensure you have a valid DRF token in the Authorization header for write operations.
- **Missing Data**: Run `make dev-fixtures` or `python manage.py loaddata entity/fixtures/*.json` to load sample data including test users.
- **Ping**: Use `GET /ping/` endpoint to verify application status and get detailed system information.

### Known Limitations

- **No Batch Ingestion**: Management commands for bulk data loading are not yet implemented.
- **No Materialized Views**: Performance optimizations through materialized views are not implemented.

## Project Structure

```
. 
├── app/                  # Django project configuration
│   ├── health.py         # Ping endpoint for health monitoring
│   └── settings.py       # Django settings
├── entity/               # Core CRM application
│   ├── fixtures/         # Sample data (entity types, details, entities, users)
│   ├── migrations/       # Database migrations (including btree_gist setup)
│   ├── models/           # Data models (SCD2 integrated)
│   │   ├── entity.py     # Main Entity model with SCD2
│   │   ├── detail.py     # EntityDetail model with SCD2
│   │   ├── type.py       # EntityType and DetailType models
│   │   └── audit.py      # AuditLog model for change tracking
│   ├── services/         # Business logic layer
│   │   ├── entity.py     # Entity business logic
│   │   ├── asof.py       # Point-in-time queries
│   │   ├── diff.py       # Temporal difference calculations
│   │   └── history.py    # Combined history retrieval
│   ├── serializers/      # DRF serializers
│   ├── views/            # DRF API views
│   │   ├── entity.py     # Main entity endpoints
│   │   └── temporal.py   # As-of and diff endpoints
│   ├── middleware.py     # Audit context middleware
│   └── urls.py           # URL routing
├── services/             # Shared utility services
│   ├── audit.py          # Audit logging service
│   ├── hash.py           # Hashdiff computation
│   ├── scd2.py           # SCD2 transition logic
│   ├── datetime.py       # Date/time utilities
│   └── pagination.py     # Pagination service
├── .env.example          # Example environment file
├── docker-compose.yml    # Docker Compose for PostgreSQL
├── docker-compose.dev.yml # Development Docker Compose
├── docker-compose.pg.yml # PostgreSQL only Docker Compose
├── docker-compose.app.yml # Application only Docker Compose
├── Dockerfile            # Docker configuration
├── Makefile              # Development commands
├── manage.py             # Django's command-line utility
├── pyproject.toml        # Python dependencies and configuration
└── README.md             # This documentation
```

## Technologies Used

- **Django 5.2+** & **Django REST Framework 3.16+**
- **PostgreSQL 15.2** with btree_gist extension
- **Docker & Docker Compose** for development environment
- **django-environ** for environment configuration
- **psycopg** for PostgreSQL database adapter
- **python-dateutil** for date/time parsing
- **Python 3.10+** (3.13 recommended)