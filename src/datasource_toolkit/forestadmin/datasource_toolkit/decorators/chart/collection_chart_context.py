from typing import List, Union

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.context.collection_context import CollectionCustomizationContext
from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.collections import Collection
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.factory import ConditionTreeFactory
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


class CollectionChartContext(CollectionCustomizationContext):
    def __init__(self, caller: User, collection: Collection, record_id: List[Union[str, int]]):
        super().__init__(collection, caller)
        self.composite_record_id = record_id

    async def get_record_id(self) -> Union[str, int]:
        if len(self.composite_record_id) > 1:
            raise DatasourceToolkitException("Collection is using a composite pk: use 'context.composite_record_id'.")

        return self.composite_record_id[0]

    async def get_record(self, fields: Union[Projection, List[str]]) -> RecordsDataAlias:
        condition_tree = ConditionTreeFactory.match_ids(self.collection.schema, [self.composite_record_id])

        records = await self.collection.list(self._caller, PaginatedFilter({"condition_tree": condition_tree}), fields)
        return records[0]
