from typing import List, Union

from forestadmin.datasource_toolkit.decorators.action.context.base import ActionContext
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.utils.records import RecordUtils


class ActionContextBulk(ActionContext):
    async def get_records_ids(self) -> List[Union[str, int]]:
        projection = Projection().with_pks(self.collection)
        records = await self.get_records(projection)
        return [RecordUtils.get_primary_key(self.collection.schema, record)[0] for record in records]
