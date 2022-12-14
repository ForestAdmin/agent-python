# Flask / SQLAlchemy

## Requirements:

To manage your demo's dependencies you should install [poetry](https://python-poetry.org/docs/).

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

## Install the dependencies

```bash
poetry install --with dev
```

## Init your database
```bash
poetry run poe init-db
```

## Populate your database with fake data
```bash
poetry run poe populate-db
```

## Run the server
```bash
poetry run poe runserver
```

## Next step
The last needed step is to onboard the project on [forestadmin](https://www.forestadmin.com/).