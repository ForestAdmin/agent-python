from typing import List, Optional, Union

from forestadmin.datasource_toolkit.decorators.action.context.base import ActionContext
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias
from forestadmin.datasource_toolkit.utils.records import RecordUtils


class ActionContextSingle(ActionContext):
    async def get_record_id(self) -> Optional[Union[str, int]]:
        projection = Projection().with_pks(self.collection)
        records = await self.get_records(projection)
        if len(records) == 0:
            return None
        ret = RecordUtils.get_primary_key(self.collection.schema, records[0])
        return ret[0] if len(ret) > 0 else None

    async def get_record(self, fields: Union[Projection, List[str]]) -> RecordsDataAlias:
        records = await self.get_records(fields)
        return records[0] if len(records) > 0 else None  # type: ignore
