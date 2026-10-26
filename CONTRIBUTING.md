# Contributing to agent-python

Thanks for helping improve the Forest Python agent. This guide covers how to report an issue, set up the repository, and get a pull request merged.

## Before you start

- **Found a bug?** Open an issue: expected behavior, actual behavior, logs, and the package versions you use (Django or Flask included).
- **Found a security issue?** Do not open a public issue. Follow the [security policy](https://github.com/ForestAdmin/.github/blob/main/SECURITY.md).
- **Planning a large change?** Open an issue first to discuss it, so your work fits the agent's direction before you write it.

## Setup

This monorepo holds one package per folder in [`src/`](./src), managed with Poetry. Python `>=3.8,<3.14` is supported.

```bash
pip install -r requirements.txt   # installs pre-commit
pre-commit install
```

Demo applications for Django and Flask live in [`src/_example/`](./src/_example).

## Tests

Run the whole suite the way the CI does:

```bash
./launch_tests_ci_like.sh
```

Or one package at a time:

```bash
cd src/<package>
poetry install --with=test
poetry run coverage run -m pytest
```

Tests must pass and the pre-commit hooks must be clean before you open a pull request.

## Commit messages

Commits follow the [Conventional Commits](https://www.conventionalcommits.org/) specification. Releases and changelogs are generated from them by semantic-release, so the type matters:

- `fix(django_agent): handle null dates` → patch release
- `feat(datasource_sqlalchemy): add the X option` → minor release
- `docs: ...`, `test: ...`, `chore: ...` → no release

## Pull requests

1. Fork the repository and create a branch from `main`.
2. Make your change, with tests.
3. Give the pull request a Conventional Commits title.
4. The CI must be green. The Forest team reviews every pull request before merging.

## Code of conduct

Everyone taking part in this project is expected to follow the [code of conduct](https://github.com/ForestAdmin/.github/blob/main/CODE_OF_CONDUCT.md).
