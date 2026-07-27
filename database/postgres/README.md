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
