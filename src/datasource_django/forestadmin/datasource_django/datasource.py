from datetime import date
from typing import Dict, List, Optional, Union

from asgiref.sync import sync_to_async
from django.apps import apps
from django.db import connections
from forestadmin.datasource_django.collection import DjangoCollection
from forestadmin.datasource_django.exception import DjangoDatasourceException
from forestadmin.datasource_django.interface import BaseDjangoDatasource
from forestadmin.datasource_toolkit.exceptions import NativeQueryException
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


class DjangoDatasource(BaseDjangoDatasource):
    def __init__(
        self,
        support_polymorphic_relations: bool = False,
        live_query_connection: Optional[Union[str, Dict[str, str]]] = None,
    ) -> None:
        """ Create a django datasource.
        More information here:
        https://docs.forestadmin.com/developer-guide-agents-python/data-sources/provided-data-sources/django


        Args:
            support_polymorphic_relations (bool, optional, default to `False`): Enable introspection over \
                polymorphic relation (AKA GenericForeignKey). Defaults to False.
            live_query_connection (Union[str, Dict[str, str]], optional, default to `None`): Set a connectionName to \
                use live queries. If a string is given, this connection will be map to django 'default' database. \
                Otherwise, you must use a dict `{'connectionName': 'DjangoDatabaseName'}`. \
                None doesn't enable this feature.
        """
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
            # This one should never occur while datasource composite works fine
            raise NativeQueryException(f"Native query connection '{connection_name}' is not known by DjangoDatasource.")

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
                raise NativeQueryException(str(e))

        return await sync_to_async(_execute_native_query)()
