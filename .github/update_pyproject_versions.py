import argparse

import toml

PYPROJECT_FILES = [
    "src/agent_toolkit/pyproject.toml",
    "src/datasource_django/pyproject.toml",
    "src/datasource_sqlalchemy/pyproject.toml",
    "src/datasource_toolkit/pyproject.toml",
    "src/django_agent/pyproject.toml",
    "src/flask_agent/pyproject.toml",
]

PACKAGE_NAMES = [
    "forestadmin-agent-toolkit",
    "forestadmin-datasource-django",
    "forestadmin-datasource-sqlalchemy",
    "forestadmin-datasource-toolkit",
    "forestadmin-django-agent",
    "forestadmin-flask-agent",
]


def mk_parser():
    parser = argparse.ArgumentParser(
        description="bump (forest-agent-python) version and dependencies versions in pyproject.toml files"
    )
    parser.add_argument("new_version", help="the version to bump to")

    return parser


def main():
    args = mk_parser().parse_args()

    for pyproject_file in PYPROJECT_FILES:
        # read pyproject
        with open(pyproject_file, "r") as file_in:
            pyproject_data = toml.load(file_in)

        # bump package version
        pyproject_data["tool"]["poetry"]["version"] = args.new_version

        # bump package dependencies
        dependencies = pyproject_data["tool"]["poetry"]["dependencies"]
        for package_name in PACKAGE_NAMES:
            if dependencies.get(package_name):
                dependencies[package_name] = f"{args.new_version}"

        # write pyproject
        with open(pyproject_file, "w") as file_out:
            toml.dump(pyproject_data, file_out)


if __name__ == "__main__":
    main()
