from typing import Any, Dict, List, Optional, Set

from forestadmin.agent_toolkit.forest_logger import ForestLogger
from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.context.collection_context import CollectionCustomizationContext
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias
from forestadmin.datasource_toolkit.validations.projection import ProjectionValidator


class FormValueObserver(Dict[str, Any]):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._used: Set[str] = set()

    def get(self, __key: str, default: Any = None) -> Any:
        self._used.add(__key)
        return super().get(__key, default)

    def __getitem__(self, __key: str) -> Any:
        self._used.add(__key)
        return super().__getitem__(__key)

    @property
    def used_keys(self) -> Set[str]:
        return self._used


class ActionContext(CollectionCustomizationContext):
    def __init__(
        self,
        collection: Collection,
        caller: User,
        form_value: RecordsDataAlias,
        filter: Filter,
        used: Optional[Set[str]] = set(),
        changed_field: Optional[str] = None,
    ):
        super(ActionContext, self).__init__(collection, caller)
        self.form_values = FormValueObserver(**form_value)
        self.filter = filter
        self._changed_field = changed_field

    @property
    def changed_field(self):
        """
        deprecated:: 1.0.0-beta14
        Use :func:`has_field_changed` instead.
        """
        ForestLogger.log(
            "warning",
            "context.changed_field == 'field_name' is now deprecated, "
            + "use context.has_field_changed('field_name') instead.",
        )
        return self._changed_field

    def has_field_changed(self, field_name):
        self.form_values._used.add(field_name)
        return field_name == self._changed_field

    async def get_records(self, fields: Projection) -> List[RecordsDataAlias]:
        ProjectionValidator.validate(self.collection, fields)
        projection = Projection(*fields)
        return await self._run_query(projection)

    async def _run_query(self, projection: Projection) -> List[RecordsDataAlias]:
        return await self.collection.list(self._caller, PaginatedFilter.from_base_filter(self.filter), projection)
