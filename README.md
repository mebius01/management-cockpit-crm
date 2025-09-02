<<<<<<< HEAD
# Management Cockpit CRM (SCD2 Core)

This project provides a robust foundation for a Management Cockpit CRM, built on Django and PostgreSQL. Its core feature is the implementation of **Slowly Changing Dimensions (SCD) Type 2** versioning directly within the main data tables, enabling full historical tracking of all data changes.

## Key Features

- **SCD Type 2 Versioning**: All entities and their details are versioned in-place using `valid_from`, `valid_to`, and `is_current` fields.
- **Temporal Queries**: Full support for "as-of" point-in-time queries and calculating differences between two time points.
- **Idempotent Operations**: Services are designed to be idempotent, preventing duplicate data entries on replay using hashdiff-based change detection.
- **Database-First Constraints**: Leverages PostgreSQL's advanced features like `Exclusion Constraints` to guarantee data integrity at the database level.
- **Service-Oriented Architecture**: Business logic is encapsulated in a dedicated service layer, separating it from the API views.
- **Comprehensive Audit Trail**: Complete logging of all changes with actor, timestamp, and before/after data.
- **Token-Based Authentication**: Secure API access with user authentication and audit context.

## Getting Started

Follow these steps to set up and run the project locally.

### Prerequisites

- Python 3.10+
- Docker & Docker Compose

### 1. Clone & Configure

First, clone the repository and navigate into the project directory.

```bash
git clone <your-repository-url>
cd trial_repo_2
```

### 2. Set Up Virtual Environment

Create and activate a virtual environment.

```bash
# Create
python -m venv .venv

# Activate (Linux/macOS)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate
```

### 3. Configure Environment Variables

Create a `.env` file in the project root by copying the example file.

```bash
cp .env.example .env
```

Now, edit the `.env` file with your local settings. The default values are configured to work with the provided Docker Compose setup.

### 4. Start the Database

Use Docker Compose to start the PostgreSQL database in the background.

```bash
docker-compose up -d
```

### 5. Install Dependencies

Install the required Python packages.
=======
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
>>>>>>> main

```bash
pip install -r requirements.txt
```

<<<<<<< HEAD
### 6. Run Database Migrations

Apply the database schema migrations.
=======
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
>>>>>>> main

```bash
python manage.py migrate
```

<<<<<<< HEAD
### 7. Load Initial Data (Fixtures)

Load the sample data, which includes entity types, detail types, sample entities, and test users.

```bash
python manage.py loaddata entity/fixtures/*.json
```

### 8. Create a Superuser (Optional)

To access the Django admin panel, create a superuser.
=======
The application will be available at: http://127.0.0.1:8000/

### 6. Create Superuser (Optional)
>>>>>>> main

```bash
python manage.py createsuperuser
```

<<<<<<< HEAD
### 9. Run the Development Server

Finally, start the Django development server.
=======
### 7. Load Initial Data (Fixtures)

The project includes initial data fixtures for entity types, detail types, entities, and entity details:

```bash
# Load all fixtures in order
python manage.py loaddata entity/fixtures/001_entity_types.json
python manage.py loaddata entity/fixtures/002_detail_types.json
python manage.py loaddata entity/fixtures/003_entities.json
python manage.py loaddata entity/fixtures/004_entity_details.json

# Or load all fixtures at once
python manage.py loaddata entity/fixtures/*.json
```

**Available fixtures:**
- `001_entity_types.json` - Basic entity type definitions
- `002_detail_types.json` - Detail type configurations
- `003_entities.json` - Sample entity records
- `004_entity_details.json` - Entity detail records

### 8. Run Development Server
>>>>>>> main

```bash
python manage.py runserver
```

<<<<<<< HEAD
The application will be available at `http://127.0.0.1:8000/`.

## API Usage & Postman

The API provides full programmatic access to the CRM's features.

### Authentication

All write operations (POST, PATCH, PUT, DELETE) require token-based authentication. Read operations (GET) are public. Test users are created by the fixtures (`005_users.json`):
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
- **List Entities**: `GET /api/v1/entities` (with optional filters: `?q=search&type=1`)
- **Get Entity Snapshot**: `GET /api/v1/entities/{entity_uid}`
- **Create Entity**: `POST /api/v1/entities` (requires authentication)
- **Update Entity**: `PATCH /api/v1/entities/{entity_uid}` (requires authentication)
- **Get Entity History**: `GET /api/v1/entities/{entity_uid}/history`
- **As-Of Query**: `GET /api/v1/entities-asof?as_of=2024-01-15T10:30:00Z`
- **Diff Query**: `GET /api/v1/diff?from=2024-01-01&to=2024-01-31`



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

=======
The application will be available at: http://127.0.0.1:8000/

### 9. Batch Ingestion from CSV

This project includes a management command for idempotent batch ingestion of entity data from a CSV file. This is useful for bulk data loads or recurring batch updates.

**CSV File Format:**

The CSV file must contain the following columns:
- `entity_uid` (optional): The stable UID of the entity. If provided, the command will attempt to update the entity. If blank, a new entity will be created.
- `display_name` (required): The display name of the entity.
- `entity_type` (required): The code for the entity type (e.g., `PERSON`, `INSTITUTION`).
- `details` (required): A JSON string representing a list of detail objects. Each object must have `detail_type` and `detail_value` keys.
- `change_ts` (optional): An ISO 8601 timestamp for the change. If not provided, the current time is used.

An example file is available at `data/sample_ingest.csv`.

**Usage:**

```bash
# Run the ingestion command
python manage.py ingest_entities data/sample_ingest.csv
```

The command will process each row, leveraging the `UpdateService` and `CreateService` to ensure SCD2 versioning and idempotency are correctly handled.

### 10. Running Tests with Pytest

This project uses `pytest` for running tests. Below are common commands for test execution.

**Run All Tests**
```bash
pytest
```

**Run Tests with Verbose Output**
```bash
pytest -v
```

**Run a Specific Test File**
```bash
pytest entity/tests/test_api_endpoints.py
```

**Run a Specific Test**
To run a single test function within a test class:
```bash
pytest entity/tests/test_api_endpoints.py::TestEntityAPIEndpoints::test_list_entities
```

**Run Tests by Marker**
Tests are organized with markers. You can run specific groups of tests using the `-m` flag.

*Available Markers:* `api`, `scd2`, `constraints`, `temporal`, `idempotency`, `unit`, `integration`, `slow`.

```bash
# Run only API tests
pytest -m api

# Run tests related to SCD2 logic
pytest -m scd2

# Run tests for constraints or temporal queries
pytest -m "constraints or temporal"
```

**Run Tests with Code Coverage**
To generate a code coverage report for the `entity` app:
```bash
pytest --cov=entity
```

**Run Tests in Parallel**
If you have `pytest-xdist` installed, you can run tests in parallel to speed up execution:
```bash
pytest -n auto
```

## Project Structure

```
.
├── app/                  # Django project configuration (settings, urls)
├── data/                 # Sample data files (e.g., for batch ingestion)
│   └── sample_ingest.csv
├── entity/               # Core CRM application
│   ├── __init__.py
│   ├── admin.py          # Django admin configurations
│   ├── apps.py
│   ├── fixtures/         # Initial data for seeding the database
│   │   ├── 001_entity_types.json
│   │   └── ...
│   ├── migrations/       # Database migrations
│   │   ├── 0001_enable_btree_gist.py
│   │   └── ...
│   ├── models/           # Data models (modularized)
│   │   ├── __init__.py
│   │   ├── entity.py     # Entity model with SCD2
│   │   ├── detail.py     # EntityDetail model with SCD2
│   │   └── type.py       # EntityType and DetailType models
│   ├── services/         # Business logic layer
│   │   ├── __init__.py
│   │   ├── create.py     # Logic for creating entities
│   │   ├── update.py     # Logic for updating entities (SCD2)
│   │   ├── asof.py       # Logic for temporal "as-of" queries
│   │   └── ...
│   ├── serializers.py    # DRF serializers for API data validation/representation
│   ├── tests/            # Test suite (modularized)
│   │   ├── __init__.py
│   │   ├── factories.py  # Test data generation using factory-boy
│   │   ├── test_api_endpoints.py
│   │   ├── test_constraints.py
│   │   └── ...
│   ├── urls.py           # URL routing for the 'entity' app
│   └── views/            # API views (modularized)
│       ├── __init__.py
│       ├── entity.py     # Views for /entities endpoint
│       ├── snapshot.py   # Views for /entities/{uid} endpoint
│       └── ...
├── .env.example          # Example environment file
├── .gitignore
├── docker-compose.yml    # Docker Compose for running PostgreSQL
├── manage.py             # Django's command-line utility
├── pytest.ini            # Pytest configuration file
├── README.md
└── requirements.txt
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

# Batch ingest from CSV
python manage.py ingest_entities <path_to_csv_file>
```

# Management Cockpit CRM Core (SCD2 In-Table)

A modular Management Cockpit foundation implementing SCD Type 2 versioning integrated into core tables. The CRM serves as the central component with Entity-centric data model supporting real-time and batch ingestion semantics.

## Architecture Overview

### Core Principles
- **Single shared core** with Entities, Entity Types, and Entity Detail values
- **SCD2 in-table versioning** using `valid_from`/`valid_to`/`is_current` columns
- **Database-first constraints** with PostgreSQL exclusion constraints preventing overlaps
- **Idempotent operations** ensuring replays don't create duplicate versions
- **As-of correctness** for all temporal queries

### Data Model

```
EntityType (PERSON, INSTITUTION, etc.)
    ↓
Entity (versioned in-place)
    ├── entity_uid (stable business identifier)
    ├── display_name
    ├── entity_type (FK)
    ├── hashdiff (for idempotency)
    ├── valid_from/valid_to/is_current (SCD2)
    └── created_at/updated_at (audit)
    ↓
EntityDetail (versioned in-place)
    ├── entity (FK)
    ├── detail_type (FK)
    ├── detail_value
    ├── hashdiff (for idempotency)
    ├── valid_from/valid_to/is_current (SCD2)
    └── created_at/updated_at (audit)
```

### Key Constraints
- **Unique current row** per `entity_uid` (partial unique index on `is_current=true`)
- **Exclusion constraints** on `(entity_uid, tstzrange(valid_from, coalesce(valid_to,'infinity')))` prevent overlaps
- **Unique current detail** per `(entity_uid, detail_code)`
- **Covering indexes** for optimal query performance

## Quick Start

### Prerequisites
- Docker and Docker Compose
- PostgreSQL 14+ with btree_gist extension

### Setup
```bash
# Clone and start the environment
git clone <repository>
cd trial_repo_2

# Start PostgreSQL and application
docker-compose up -d

# Run migrations
python manage.py migrate

# Load fixtures (optional)
python manage.py loaddata entity/fixtures/*.json

# Start development server
python manage.py runserver
```

## API Reference

Base URL: `http://localhost:8000/api/v1/`

### Entity Management

#### List Entities (Current)
```bash
# Basic list
curl -X GET "http://localhost:8000/api/v1/entities"

# Search by name
curl -X GET "http://localhost:8000/api/v1/entities?q=john"

# Filter by entity type
curl -X GET "http://localhost:8000/api/v1/entities?entity_type=PERSON"

# Filter by detail
curl -X GET "http://localhost:8000/api/v1/entities?email=john@example.com"
```

#### Create Entity
```bash
curl -X POST "http://localhost:8000/api/v1/entities" \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "John Doe",
    "entity_type": "PERSON",
    "details": [
      {
        "detail_type": "email",
        "detail_value": "john.doe@example.com"
      },
      {
        "detail_type": "phone",
        "detail_value": "+1-555-0123"
      }
    ]
  }'
```

#### Get Entity Snapshot (Current)
```bash
curl -X GET "http://localhost:8000/api/v1/entities/{entity_uid}"
```

#### Update Entity (SCD2 Transition)
```bash
curl -X PATCH "http://localhost:8000/api/v1/entities/{entity_uid}" \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "John Smith",
    "details": [
      {
        "detail_type": "email",
        "detail_value": "john.smith@newcompany.com"
      }
    ]
  }'
```

### Temporal Queries

#### As-Of Query (Point-in-Time)
```bash
# Entities as they were on specific date
curl -X GET "http://localhost:8000/api/v1/entities-asof?as_of=2024-01-15"

# With time
curl -X GET "http://localhost:8000/api/v1/entities-asof?as_of=2024-01-15T10:30:00Z"
```

#### Entity History
```bash
# Complete history for an entity
curl -X GET "http://localhost:8000/api/v1/entities/{entity_uid}/history"
```

#### Diff Between Time Points
```bash
# Changes between two dates
curl -X GET "http://localhost:8000/api/v1/diff?from=2024-01-01&to=2024-01-31"

# With specific times
curl -X GET "http://localhost:8000/api/v1/diff?from=2024-01-01T00:00:00Z&to=2024-01-31T23:59:59Z"
```

## Performance Analysis

### Key Query Patterns and Indexes

#### 1. Current Entity Lookup
```sql
-- Query: Get current entity by UID
SELECT * FROM entity WHERE entity_uid = ? AND is_current = true;

-- Index: entity_uid_current_covering_idx
-- Covers: entity_uid, is_current + display_name, entity_type, valid_from
```

#### 2. As-Of Entity Query
```sql
-- Query: Entities valid at specific time
SELECT * FROM entity 
WHERE valid_from <= ? 
  AND (valid_to > ? OR valid_to IS NULL);

-- Index: entity_valid_from_covering_idx  
-- Covers: valid_from + entity_uid, display_name, entity_type, is_current
```

#### 3. Entity Details Fetch
```sql
-- Query: Current details for entity
SELECT * FROM entitydetail 
WHERE entity_id = ? AND is_current = true;

-- Index: detail_entity_current_covering_idx
-- Covers: entity, is_current + detail_type, detail_value, valid_from
```

#### 4. Search by Name
```sql
-- Query: Search entities by display name
SELECT * FROM entity 
WHERE display_name ILIKE ? AND is_current = true;

-- Index: entity_name_covering_idx
-- Covers: display_name + entity_uid, entity_type, is_current, valid_from
```

### EXPLAIN ANALYZE Examples

#### Current Entity List Query
```sql
EXPLAIN ANALYZE
SELECT e.entity_uid, e.display_name, et.name as entity_type_name
FROM entity e
JOIN entitytype et ON e.entity_type_id = et.id
WHERE e.is_current = true
ORDER BY e.display_name
LIMIT 20;

-- Expected: Index Scan using entity_current_type_covering_idx
-- Cost: ~0.43..8.45 rows=20 (actual time=0.023..0.045 rows=20)
```

#### As-Of Query Performance
>>>>>>> main
```sql
EXPLAIN ANALYZE
SELECT e.entity_uid, e.display_name, e.valid_from
FROM entity e
WHERE e.valid_from <= '2024-01-15T00:00:00Z'
  AND (e.valid_to > '2024-01-15T00:00:00Z' OR e.valid_to IS NULL)
ORDER BY e.entity_uid;

<<<<<<< HEAD
-- Expected Result: Uses an Index Scan on entity_valid_from_covering_idx for high performance.
```

### Troubleshooting

- **Overlapping Periods Error**: This is prevented by the database exclusion constraints, but if it occurs, it indicates a logic error in the application code that tried to create an invalid state.
- **Poor Performance**: Use `EXPLAIN ANALYZE` on your query to ensure the correct covering indexes are being used.
- **Authentication Issues**: Ensure you have a valid token in the Authorization header for write operations.
- **Missing Data**: Run `python manage.py loaddata entity/fixtures/*.json` to load sample data including test users.

### Known Limitations

- **No Batch Ingestion**: Management commands for bulk data loading are not yet implemented.
- **No Materialized Views**: Performance optimizations through materialized views are not implemented.

## Project Structure

```
. 
├── app/                  # Django project configuration
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
├── manage.py             # Django's command-line utility
├── pytest.ini            # Pytest configuration
├── requirements.txt      # Python dependencies
└── README.md             # This documentation
```

## Technologies Used

- **Django 5.0.1** & **Django REST Framework 3.14.0**
- **PostgreSQL 15.2** with btree_gist extension
- **Docker & Docker Compose** for development environment
- **django-environ** for environment configuration
- **psycopg** for PostgreSQL database adapter
- **python-dateutil** for date/time parsing
=======
-- Expected: Index Scan using entity_valid_from_covering_idx
-- Cost: ~0.42..12.89 rows=50 (actual time=0.034..0.156 rows=50)
```

## Design Walkthrough

### SCD2 Implementation Strategy

1. **In-Table Versioning**: Each table contains all versions with temporal columns
2. **Exclusion Constraints**: Prevent overlapping validity periods using PostgreSQL GiST
3. **Partial Unique Indexes**: Ensure only one current record per business key
4. **Covering Indexes**: Include frequently accessed columns to avoid table lookups

### Idempotency Mechanism

1. **Hashdiff Computation**: Normalized business values → SHA256 hash
2. **Delta Detection**: Compare hashdiff before creating new versions
3. **Transactional Close-and-Open**: Atomic operations ensure consistency
4. **Change Timestamp**: Support for replay scenarios with specific timestamps

### Service Layer Architecture

```
Views (DRF) → Services → Models (Django ORM) → Database (PostgreSQL)
     ↓
- EntityAPIView      - ListService        - Entity           - SCD2 Tables
- SnapshotAPIView    - CreateService      - EntityDetail     - Exclusion Constraints  
- AsOfAPIView        - UpdateService      - EntityType       - Covering Indexes
- DiffAPIView        - AsOfService        - DetailType       - Audit Timestamps
- HistoryAPIView     - DiffService
                     - GetService
                     - HistoryService
```

### Extensibility for Future Modules

1. **Shared Entity UID**: Cross-module joins via stable `entity_uid`
2. **Shared SCD2 Semantics**: Consistent as-of reconstruction across modules
3. **Shared Validation**: `DateTimeValidationService` for temporal parameters
4. **Modular Services**: Each service handles specific business logic

## Data Model Details

### Entity Constraints
```sql
-- Unique current entity per UID
CONSTRAINT unique_current_entity 
UNIQUE (entity_uid) WHERE is_current = true

-- Prevent overlapping validity periods
CONSTRAINT exclude_overlapping_entities 
EXCLUDE USING gist (
  entity_uid WITH =,
  tstzrange(valid_from, COALESCE(valid_to, 'infinity'::timestamptz), '[)') WITH &&
)
```

### EntityDetail Constraints
```sql
-- Unique current detail per entity+type
CONSTRAINT unique_current_entity_detail 
UNIQUE (entity_id, detail_type_id) WHERE is_current = true

-- Prevent overlapping detail validity periods
CONSTRAINT exclude_overlapping_details 
EXCLUDE USING gist (
  entity_id WITH =,
  detail_type_id WITH =,
  tstzrange(valid_from, COALESCE(valid_to, 'infinity'::timestamptz), '[)') WITH &&
)
```

## Testing Strategy

### Required Test Categories
1. **SCD2 Transition Tests**: Verify proper versioning behavior
2. **API Integration Tests**: Test all endpoints with various scenarios
3. **Idempotency Tests**: Ensure replays don't create duplicates
4. **Constraint Violation Tests**: Verify database constraints work
5. **Temporal Query Tests**: As-of and diff functionality

### Example Test Scenarios
```python
# SCD2 Transition Test
def test_entity_update_creates_new_version():
    # Create entity
    # Update entity
    # Assert: 2 versions exist, old is closed, new is current

# Idempotency Test  
def test_identical_update_is_noop():
    # Create entity
    # Update with same data twice
    # Assert: Only 1 version exists

# As-Of Test
def test_as_of_query_returns_correct_version():
    # Create entity at T1
    # Update entity at T2  
    # Query as-of T1.5
    # Assert: Returns T1 version
```

## Development Guidelines

### Adding New Entity Types
1. Add entry to `EntityType` fixture
2. Update API documentation
3. Add validation if needed

### Adding New Detail Types
1. Add entry to `DetailType` fixture
2. Consider indexing strategy for new detail
3. Update search/filter logic if applicable

### Performance Considerations
- Use covering indexes for new query patterns
- Monitor exclusion constraint performance
- Consider materialized views for complex aggregations
- Profile as-of queries with large datasets

## Troubleshooting

### Common Issues
1. **Overlapping Periods**: Check exclusion constraints
2. **Performance**: Verify covering indexes are used
3. **Idempotency**: Check hashdiff computation
4. **Temporal Queries**: Ensure proper timezone handling

### Debug Queries
```sql
-- Check for constraint violations
SELECT entity_uid, COUNT(*) 
FROM entity 
WHERE is_current = true 
GROUP BY entity_uid 
HAVING COUNT(*) > 1;

-- Verify index usage
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM entity WHERE is_current = true;
```

This implementation provides a solid foundation for the Management Cockpit with proper SCD2 semantics, idempotent operations, and extensibility for future modules.
>>>>>>> main
