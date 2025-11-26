# Take-Home Challenge: TracOS ↔ Client Integration Flow

## Introduction

This repository contains a technical assesment to evaluate your skills on a simulated scenario of an integration between Tractian's CMMS (TracOS) and a customer's ERP.

The test objective is to build an asynchronous Python service that simulates an integration between our CMMS (TracOS) and a customer's ERP software, containing both an inbound (client → TracOS) and outbound (TracOS → client) flows. The integration focus is to sync work orders between the systems.

The customer's system will be simulated by JSON files representing API responses. Our system will be represented by a MongoDB instance.

Create at least three modules: one to handle read/write on our system (TracOS), one to handle read/write on the customer's system and one to handle translations between systems. The main objective by creating these modules is to have a project where it is easy to add an integration to another system, without needing to modify the existing modules, only expanding them.

Notes: 
- The dependency management in this project must be done using Poetry.
- There is a docker-compose to create a MongoDB instance, figure out how to use it.
- There is a setup.py file that creates samples workorders on our system and on the customer's system (JSON file). You need to run this after you create the MongoDB instance with docker-compose. That file also has some tips on how to build your own code.

The main objectives of this assesment are to demonstrate:

- Clarity in functional requirements  
- Attention to expected system behavior  
- Code organization for future maintenance  

---

## What the System Must Do

1. **Inbound**  
   - Read JSON files (simulating the client's API response) from an input folder  
   - For each work order:  
     - Validate required fields (e.g., `id`, `status`, `createdAt`)  
     - Translate payload from client format → TracOS format  
     - Insert or update the record in a MongoDB collection  

2. **Outbound**  
   - Query MongoDB for work orders with `isSynced = false`  
   - For each record:  
     - Translate from TracOS format → client format  
     - Write the output JSON into an output folder, ready to "send" to the client  
     - Mark the document in MongoDB with `isSynced = true` and set a `syncedAt` timestamp  

3. **Translation / Normalization**  
   - Normalize date fields to UTC ISO 8601  
   - Map enums/status values (e.g., client uses `"NEW"`, TracOS uses `"created"`)  

4. **Resilience**  
   - Clear success and error logs without unreadable stack traces  
   - Handle I/O errors (corrupted file, permission issues) gracefully  
   - Simple retry or reconnect logic for MongoDB failures  

---

## Non-Technical Requirements

- **Complete README**: explain how to run and a summary of the chosen architecture
- **Configuration via environment variables**:  
  - `MONGO_URI` → MongoDB connection string  
  - `DATA_INBOUND_DIR` and `DATA_OUTBOUND_DIR` → input/output folders  
- **Basic tests**:  
  - Sample input and output JSON  
  - End-to-end workflow verification (full coverage not required)  
- **Best practices**: informative logging, readable code, simple modularity  

---

## Deliverables

1. Git repository forking this repository, containing:  
   - Running `main.py` should start the entire pipeline  
   - Clear modules for:  
     - Read/write on our system
     - Read/write on customer's system
     - Translating data between systems
2. Complete the `README.md` file with the folder structure and a general overview of how the system works.  
3. At least **one** automated test with `pytest` testing the end-to-end flow  

---
## Evaluation Criteria

- **Functionality**: inbound/outbound flows work as described  
- **Robustness**: proper error handling and logging  
- **Clarity**: self-explanatory, comprehensive README  
- **Maintainability**: clear separation of concerns, modular code  
- **Tests**: basic coverage of the main workflow  

---

## Setting Up The Project

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Poetry for dependency management

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd integrations-engineering-code-assesment
   ```

2. **Install dependencies with Poetry**
   ```bash
   # Install Poetry if you don't have it
   curl -sSL https://install.python-poetry.org | python3 -
   
   # Install dependencies
   poetry install
   ```

3. **Start MongoDB using Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Run the setup script to initialize sample data**
   ```bash
   poetry run python setup.py
   ```

5. **Configure environment variables**
   ```bash
   # Create a .env file or export directly in your shell
   echo "MONGO_URI=mongodb://localhost:27017/tractian" > .env
   echo "DATA_INBOUND_DIR=./data/inbound" >> .env
   echo "DATA_OUTBOUND_DIR=./data/outbound" >> .env
   ```

## Project Structure

```
integrations-engineering-code-assesment/
├── docker-compose.yml       # MongoDB container configuration
├── pyproject.toml           # Poetry configuration
├── setup.py                 # Setup script for sample data
├── data/                    # Data directories
│   ├── inbound/             # Client → TracOS JSON files
│   └── outbound/            # TracOS → Client JSON files
├── src/                     # Source code
│   └── main.py              # Main execution script
│   ...
└── tests/                   # Test directory
|   ...
```

## Running the Application

1. **Execute the main script**
   ```bash
   python src/main.py
   ```

## Testing

Run the tests with:
```bash
poetry run pytest
```

## Troubleshooting

- **MongoDB Connection Issues**: Ensure Docker is running and the MongoDB container is up with `docker ps`
- **Missing Dependencies**: Verify Poetry environment is activated or run `poetry install` again
- **Permission Issues**: Check file permissions for data directories


