from io import StringIO

from forestadmin.datasource_toolkit.decorators.action.result_builder import ResultBuilder
from forestadmin.fastapi_agent.agent import FastAPIAgent


async def return_file(context, result_builder: ResultBuilder):
    ret = StringIO("bla bla")
    return result_builder.file(ret, "blssa.csv", "text/csvs")


def customize_forest(agent: FastAPIAgent):
    agent.customize_collection("address").add_action(
        "file_action", {"scope": "Global", "generate_file": True, "execute": return_file}
    )
