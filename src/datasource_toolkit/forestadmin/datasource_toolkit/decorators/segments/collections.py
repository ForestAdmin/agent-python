from typing import Any, Awaitable, Callable, Dict, Optional, Union, cast

from forestadmin.datasource_toolkit.context.collection_context import CollectionCustomizationContext
from forestadmin.datasource_toolkit.interfaces.collections import Collection
from forestadmin.datasource_toolkit.interfaces.models.collections import CollectionSchema
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.factory import ConditionTreeFactory
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import ConditionTree
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter

SegmentAlias = Callable[[CollectionCustomizationContext], Union[ConditionTree, Awaitable[ConditionTree]]]


class SegmentMixin:
    mark_schema_as_dirty: Callable[[], None]

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._segments: Dict[str, SegmentAlias] = {}

    def add_segment(self, name: str, segment: SegmentAlias):
        self._segments[name] = segment
        self.mark_schema_as_dirty()

    @property
    def schema(self) -> CollectionSchema:
        schema: CollectionSchema = super(SegmentMixin, self).schema  # type: ignore
        schema["segments"] = [*schema["segments"], *self._segments.keys()]
        return schema

    async def _refine_filter(
        self, filter: Union[Optional[PaginatedFilter], Optional[Filter]]
    ) -> Optional[Union[PaginatedFilter, Filter]]:
        filter = cast(SegmentMixin, await super()._refine_filter(filter))  # type: ignore
        if not filter:
            return None

        if filter.segment and filter.segment in self._segments:
            definition = self._segments[filter.segment]
            context = CollectionCustomizationContext(cast(Collection, self), filter.timezone)
            condition_tree_segment = definition(context)
            if isinstance(condition_tree_segment, Awaitable):
                condition_tree_segment = await condition_tree_segment

            trees = [condition_tree_segment]
            if filter.condition_tree:
                trees.append(filter.condition_tree)
            condition_tree = ConditionTreeFactory.intersect(trees)
            filter = filter.override({"condition_tree": condition_tree, "segment": None})
        return filter
