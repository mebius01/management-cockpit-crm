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

```bash
pip install -r requirements.txt
```

### 6. Run Database Migrations

Apply the database schema migrations.

```bash
python manage.py migrate
```

### 7. Load Initial Data (Fixtures)

Load the sample data, which includes entity types, detail types, sample entities, and test users.

```bash
python manage.py loaddata entity/fixtures/*.json
```

### 8. Create a Superuser (Optional)

To access the Django admin panel, create a superuser.

```bash
python manage.py createsuperuser
```

### 9. Run the Development Server

Finally, start the Django development server.

```bash
python manage.py runserver
```

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