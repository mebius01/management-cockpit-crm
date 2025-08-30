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

```bash
python manage.py runserver
```

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
```sql
EXPLAIN ANALYZE
SELECT e.entity_uid, e.display_name, e.valid_from
FROM entity e
WHERE e.valid_from <= '2024-01-15T00:00:00Z'
  AND (e.valid_to > '2024-01-15T00:00:00Z' OR e.valid_to IS NULL)
ORDER BY e.entity_uid;

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