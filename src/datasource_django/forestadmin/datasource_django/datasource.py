from datetime import date
from typing import Dict, List, Optional, Union

from asgiref.sync import sync_to_async
from django.apps import apps
from django.db import connections
from forestadmin.agent_toolkit.forest_logger import ForestLogger
from forestadmin.datasource_django.collection import DjangoCollection
from forestadmin.datasource_django.exception import DjangoDatasourceException
from forestadmin.datasource_django.interface import BaseDjangoDatasource
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


class DjangoDatasource(BaseDjangoDatasource):
    def __init__(
        self,
        support_polymorphic_relations: bool = False,
        live_query_connection: Optional[Union[str, Dict[str, str]]] = None,
    ) -> None:
        self._django_live_query_connections: Dict[str, str] = self._handle_live_query_connections_param(
            live_query_connection
        )
        super().__init__([*self._django_live_query_connections.keys()])

        self.support_polymorphic_relations = support_polymorphic_relations
        self._create_collections()

    def _handle_live_query_connections_param(
        self, live_query_connections: Optional[Union[str, Dict[str, str]]]
    ) -> Dict[str, str]:
        if live_query_connections is None:
            return {}

        if isinstance(live_query_connections, str):
            ret = {live_query_connections: "default"}
            if len(connections.all()) > 1:
                ForestLogger.log(
                    "info",
                    f"You enabled live query as {live_query_connections} for django 'default' database."
                    " To use it over multiple databases, read the related documentation here: http://link.",
                    # TODO: link
                )
        else:
            ret = live_query_connections

        for forest_name, db_name in ret.items():
            if db_name not in connections:
                raise DjangoDatasourceException(
                    f"Connection to database '{db_name}' for alias '{forest_name}' is not found in django databases. "
                    f"Existing connections are {','.join([*connections])}"
                )
        return ret

    def _create_collections(self):
        models = apps.get_models(include_auto_created=True)
        for model in models:
            if model._meta.proxy is False:
                collection = DjangoCollection(self, model, self.support_polymorphic_relations)
                self.add_collection(collection)

    async def execute_native_query(
        self, connection_name: str, native_query: str, parameters: Dict[str, str]
    ) -> List[RecordsDataAlias]:
        if connection_name not in self._django_live_query_connections.keys():
            # TODO: verify
            # This one should never occur while datasource composite works fine
            raise DjangoDatasourceException(
                f"Native query connection '{connection_name}' is not known by DjangoDatasource."
            )

        if self._django_live_query_connections[connection_name] not in connections:
            # This one should never occur
            # TODO: verify
            raise DjangoDatasourceException(
                f"Connection to database '{self._django_live_query_connections[connection_name]}' for alias "
                f"'{connection_name}' is not found in django connections. "
                f"Existing connections are {','.join([*connections])}"
            )

        def _execute_native_query():
            cursor = connections[self._django_live_query_connections[connection_name]].cursor()  # type: ignore
            try:
                # replace '\%' by '%%'
                # %(var)s is already the correct  syntax
                rows = cursor.execute(native_query.replace("\\%", "%%"), parameters)

                ret = []
                for row in rows:
                    return_row = {}
                    for i, field_name in enumerate(rows.description):
                        value = row[i]
                        if isinstance(value, date):
                            value = value.isoformat()
                        return_row[field_name[0]] = value
                    ret.append(return_row)
                return ret
            except Exception as e:
                # TODO: verify
                raise DjangoDatasourceException(str(e))

        return await sync_to_async(_execute_native_query)()
