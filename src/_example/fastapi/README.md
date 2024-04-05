# Flask / SQLAlchemy

## Requirements

To manage your demo's dependencies you should install [poetry](https://python-poetry.org/docs/).

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

### Already met problems

- If you're having SSL issue with Python while installing poetry, visit this link: <https://matduggan.com/til-python-3-6-and-up-is-broken-on-mac/>
- Make sure poetry is in your $PATH, sometimes on mac there is conflict between python installed graphically and installed with brew. You  can use these commands to help you to find the problems

```bash
which python
which python3
which python3.10
echo "PATH=$PATH;~/Library/Application Support/pypoetry/venv/bin" >> ~/.zshrc  # this is default installation path for poetry on mac
```

## (Optional) Auto-load .env files with poetry

```bash
poetry self add poetry-dotenv-plugin
```

## create a virtual env

```bash
python -m venv venv  # the last 'venv' is the relative path where you want your virtual env
```

## activate it

```bash
source venv/bin/activate  # adapt venv with the path previously used
```

## Install the dependencies

```bash
poetry install
```

## Init your database

```bash
python ./bin/db.py create
```

## Populate your database with fake data

```bash
python ./bin/db.py seed

```

## Run the server

```bash
python ./main.py
```

## Next step

The last needed step is to onboard the project on [forestadmin](https://www.forestadmin.com/)
