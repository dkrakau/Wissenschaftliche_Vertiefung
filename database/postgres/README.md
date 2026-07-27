## Run docker container

```
docker compose up -d
```

## Connect to postgres docker container

```
docker exec -it postgres /bin/bash
```

## Conntect to postgres database using psql

```
psql -U admin -h localhost -d postgres
```

## Script to build database

```
psql -U postgres -h localhost -d postgres -f /scripts/create_database.sql
```

## Script to build schema and tables

```
psql -U postgres -h localhost -d postgres -f /scripts/create_schema.sql
```
