from datetime import date
from typing import List, Optional

from asgiref.sync import sync_to_async
from django.apps import apps
from django.db import connection
from forestadmin.datasource_django.collection import DjangoCollection
from forestadmin.datasource_django.exception import DjangoDatasourceException
from forestadmin.datasource_django.interface import BaseDjangoDatasource
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


class DjangoDatasource(BaseDjangoDatasource):
    def __init__(self, support_polymorphic_relations: bool = False, name: Optional[str] = None) -> None:
        super().__init__(name)
        self.support_polymorphic_relations = support_polymorphic_relations
        self._create_collections()
        self.enable_native_query()

    def _create_collections(self):
        models = apps.get_models(include_auto_created=True)
        for model in models:
            if model._meta.proxy is False:
                collection = DjangoCollection(self, model, self.support_polymorphic_relations)
                self.add_collection(collection)

    async def execute_native_query(self, native_query: str) -> List[RecordsDataAlias]:
        def _execute_native_query():
            cursor = connection.cursor()
            try:
                rows = cursor.execute(native_query)
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
