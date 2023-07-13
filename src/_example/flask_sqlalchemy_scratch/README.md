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

## To add a custom root certificate in the trust bundle :
If you use a local forest-admin-server for dev
```bash
rootCaPath=~/git/forestadmin-server/docker/etc/nginx/ssl/rootCA.pem  # adapt to your need

export SSL_CERT_FILE=$rootCaPath  # for aiohttp
export REQUESTS_CA_BUNDLE=$rootCaPath  # for oic (openId client)
```

## Run the server
```bash
poetry run poe runserver
```

## Next step
The last needed step is to onboard the project on [forestadmin](https://www.forestadmin.com/).