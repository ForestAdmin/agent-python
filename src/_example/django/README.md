# django

## See django version lifecycle
[https://endoflife.date/django](https://endoflife.date/django)

## Using docker

First you need to create a `.env` file from [.env.docker.sample](./.env.docker.sample) file to add your `FOREST_ENV_SECRET` and `FOREST_AUTH_SECRET`

Normally with docker, you just have a few command to use, in the correct folder:

```bash
cd src/_example/django

docker compose up -d # to start in background
# Example project is now running on port 8000 with auto reload

docker compose logs -f # to see the output

docker compose down # to cleanup
```

⚠️ If you already have a [`.env`](./.env) at the root of this example project, it will be used, overriding environment variables defined in the [docker-compose.yaml](./docker-compose.yaml) file.

## Setup a dev environment on your machine

### Requirements

To manage your demo's dependencies you should install [poetry](https://python-poetry.org/docs/).

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

#### Already met problems

- If you're having SSL issue with Python while installing poetry, visit this link: <https://matduggan.com/til-python-3-6-and-up-is-broken-on-mac/>
- Make sure poetry is in your $PATH, sometimes on mac there is conflict between python installed graphically and installed with brew. You  can use these commands to help you to find the problems

```bash
which python
which python3
which python3.10
echo "PATH=$PATH;~/Library/Application Support/pypoetry/venv/bin" >> ~/.zshrc  # this is default installation path for poetry on mac
```

### (Optional) Auto-load .env files with poetry

```bash
poetry self add poetry-dotenv-plugin
```

### create a virtual env

```bash
python -m venv venv  # the last 'venv' is the relative path where you want your virtual env
```

### activate it

```bash
source venv/bin/activate  # adapt venv with the path previously used
```

### Install the dependencies

```bash
poetry install --with dev
```

### Init your database

```bash
poetry run poe init-db
```

### Populate your database with fake data

```bash
poetry run poe populate-db
```

### Run the server

```bash
poetry run poe runserver
```

### Next step

The last needed step is to onboard the project on [forestadmin](https://www.forestadmin.com/)
