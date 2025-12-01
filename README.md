- Starting the project environment
```bash
cp .env.example .env

docker compose up -d --build

docker exec app python setup.py

docker exec app python src/main.py

```

- Querying the results
```bash
docker exec -it tractian-mongo sh

mongosh

use tractian

db.workorders.find()

# db.workorders.drop()

```