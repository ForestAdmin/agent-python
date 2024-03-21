from typing import Any, Awaitable, Callable, Dict, Optional, Union, cast

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.context.collection_context import CollectionCustomizationContext
from forestadmin.datasource_toolkit.decorators.collection_decorator import CollectionDecorator
from forestadmin.datasource_toolkit.interfaces.collections import Collection
from forestadmin.datasource_toolkit.interfaces.models.collections import CollectionSchema
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.factory import ConditionTreeFactory
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import ConditionTree
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.utils.user_callable import call_user_function

SegmentAlias = Callable[[CollectionCustomizationContext], Union[ConditionTree, Awaitable[ConditionTree]]]


class SegmentCollectionDecorator(CollectionDecorator):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._segments: Dict[str, SegmentAlias] = {}

    def add_segment(self, name: str, segment: SegmentAlias):
        self._segments[name] = segment
        self.mark_schema_as_dirty()

    def _refine_schema(self, sub_schema: CollectionSchema) -> CollectionSchema:
        return {**sub_schema, "segments": [*self._segments.keys()]}

    async def _refine_filter(
        self, caller: User, _filter: Union[Optional[PaginatedFilter], Optional[Filter]]
    ) -> Optional[Union[PaginatedFilter, Filter]]:
        _filter = await super()._refine_filter(caller, _filter)  # type: ignore
        if not _filter:
            return None

        if _filter.segment and _filter.segment in self._segments:
            definition = self._segments[_filter.segment]
            context = CollectionCustomizationContext(cast(Collection, self), caller)
            condition_tree_segment = await call_user_function(definition, context)

            if isinstance(condition_tree_segment, dict):
                condition_tree_segment = ConditionTreeFactory.from_plain_object(condition_tree_segment)

            trees = [condition_tree_segment]
            if _filter.condition_tree:
                trees.append(_filter.condition_tree)
            condition_tree = ConditionTreeFactory.intersect(trees)
            _filter = _filter.override({"condition_tree": condition_tree, "segment": None})
        return _filter
