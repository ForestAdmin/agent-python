import enum
import os
from typing import Dict, List

import toml


class Dependencies(enum.Enum):
    DATASOURCE_TOOLKIT = "datasource_toolkit"
    AGENT_TOOLKIT = "agent_toolkit"


DATASOURCE_TOOLKIT_PYPROJECT = "./src/datasource_toolkit/pyproject.toml"
DATASOURCE_SQLALCHEMY_PYPROJECT = "./src/datasource_sqlalchemy/pyproject.toml"
AGENT_TOOLKIT_PYPROJECT = "./src/agent_toolkit/pyproject.toml"
FLASK_AGENT_PYPROJECT = "./src/flask_agent/pyproject.toml"

PYPROJECTS: Dict[str, List[Dependencies]] = {
    DATASOURCE_TOOLKIT_PYPROJECT: [],
    AGENT_TOOLKIT_PYPROJECT: [
        Dependencies.DATASOURCE_TOOLKIT,
    ],
    DATASOURCE_SQLALCHEMY_PYPROJECT: [Dependencies.DATASOURCE_TOOLKIT],
    FLASK_AGENT_PYPROJECT: [
        Dependencies.DATASOURCE_TOOLKIT,
        Dependencies.AGENT_TOOLKIT,
    ],
}


if __name__ == "__main__":
    for pyproject, dependencies in PYPROJECTS.items():
        data = {}
        with open(pyproject, "r") as f:
            data = toml.load(f)
            version = data["tool"]["poetry"]["version"]  # version is updated by a github action
            if Dependencies.DATASOURCE_TOOLKIT in dependencies:
                data["tool"]["poetry"]["dependencies"]["forestadmin-datasource-toolkit"] = f"^{version}"
            if Dependencies.AGENT_TOOLKIT in dependencies:
                data["tool"]["poetry"]["dependencies"]["forestadmin-agent-toolkit"] = f"^{version}"
        with open(pyproject, "w") as f:
            f.truncate(0)
            toml.dump(data, f)
        directory = os.path.split(pyproject)[0]
        os.system(f"cd {directory} && poetry lock --no-update && cd -")
