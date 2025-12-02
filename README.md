# TracOS ↔ Client Integration Flow

An asynchronous Python service that synchronizes work orders between Tractian's CMMS (TracOS) and a customer's ERP system. The integration supports bidirectional data flow with automatic format translation and robust error handling.

## Quick Start

**Prerequisites:** Docker and Docker Compose

```bash
# Clone and navigate to project
git clone https://github.com/DouglasKosvoski/tractian
cd tractian

# Setup environment and start services
cp .env.example .env
docker compose up -d --build

# Generate sample data and run integration
docker exec app python setup.py
docker exec app python src/main.py

# Run tests
docker exec app poetry run pytest tests/

# Run tests with coverage
docker exec app poetry run pytest --cov=src --cov-report=term-missing
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_DRIVER` | Database driver to use | `mongodb` |
| `MONGO_URI` | MongoDB connection string | `mongodb://localhost:27017` |
| `MONGO_DATABASE` | Database name | `tractian` |
| `MONGO_COLLECTION` | Collection name for workorders | `workorders` |
| `DATA_INBOUND_DIR` | Directory for inbound JSON files | `data/inbound` |
| `DATA_OUTBOUND_DIR` | Directory for outbound JSON files | `data/outbound` |
| `LOG_LEVEL` | Logging verbosity | `DEBUG` |

---

## Data Flow

### Inbound Flow (Client → TracOS)

1. Read JSON files from `DATA_INBOUND_DIR`
2. Validate required fields (`orderNo`, `status`, `creationDate`, etc.)
3. Translate payload from Client format to TracOS format
4. Normalize dates to UTC ISO 8601
5. Map status enums (e.g., `"NEW"` → `"created"`)
6. Insert or update records in MongoDB

### Outbound Flow (TracOS → Client)

1. Query MongoDB for workorders with `isSynced = false`
2. Validate TracOS workorder format
3. Translate from TracOS format to Client format
4. Write JSON files to `DATA_OUTBOUND_DIR`
5. Mark documents as synced (`isSynced = true`, `syncedAt` timestamp)

---

## Status Mappings

| Client Status | TracOS Status |
|---------------|---------------|
| `NEW` | `created` |
| `PENDING` | `pending` |
| `IN_PROGRESS` | `in_progress` |
| `ON_HOLD` | `on_hold` |
| `COMPLETED` | `completed` |
| `CANCELLED` | `cancelled` |
| `DELETED` | `deleted` |

The system also supports legacy boolean flags (`isDone`, `isCanceled`, etc.) for backward compatibility.

---

## Architecture

```
src/
├── main.py                          # Application entrypoint
├── adapters/                        # Infrastructure adapters
│   ├── db.py                        # MongoDB connection with retry logic
│   └── filesystem.py                # JSON file I/O with atomic writes
└── integration/
    ├── types.py                     # TypedDict definitions for type safety
    ├── flows/                       # Orchestration layer
    │   ├── client_to_tracos.py      # Inbound flow (Client → TracOS)
    │   └── tracos_to_client.py      # Outbound flow (TracOS → Client)
    ├── system/                      # System-specific repositories
    │   ├── client/
    │   │   └── repository.py        # Client filesystem operations
    │   └── tracos/
    │       └── repository.py        # TracOS MongoDB operations
    └── translators/                 # Data transformation layer
        ├── client_to_tracos.py      # Client → TracOS format translation
        ├── tracos_to_client.py      # TracOS → Client format translation
        └── status_mappings.py       # Status enum mappings between systems
```

### Layer Responsibilities

| Layer | Purpose |
|-------|---------|
| **Adapters** | Low-level infrastructure concerns (database connections, file I/O) |
| **Flows** | Orchestrates the sync process between systems |
| **Repositories** | System-specific data access (CRUD operations) |
| **Translators** | Format conversion and field mapping between systems |
| **Types** | Shared type definitions for type safety |

### Design Principles

- **Modularity**: Each system (Client, TracOS) has isolated repositories and translators
- **Extensibility**: Adding a new integration only requires new repository and translator modules
- **Resilience**: Retry logic for database connections, graceful error handling for I/O operations
- **Type Safety**: TypedDict definitions ensure consistent data structures

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **MongoDB Connection Issues** | Ensure Docker is running: `docker ps` should show the MongoDB container |
| **Missing Dependencies** | Run `poetry install` to reinstall dependencies |
| **Permission Issues** | Check file permissions for data directories |
| **Import Errors** | Run from project root or use `poetry run python src/main.py` |

---

## Extending the System

To add a new integration with another system:

1. **Create a new repository** in `src/integration/system/<new_system>/repository.py`
2. **Create translators** in `src/integration/translators/` for bidirectional conversion
3. **Create flow classes** in `src/integration/flows/` to orchestrate the sync
4. **Update status mappings** if the new system uses different status values
5. **Add type definitions** to `src/integration/types.py`

The modular architecture ensures existing modules remain unchanged when adding new integrations.
