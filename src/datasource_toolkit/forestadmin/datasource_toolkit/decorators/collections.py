from typing import Any

from forestadmin.datasource_toolkit.decorators.action.collections import ActionMixin
from forestadmin.datasource_toolkit.decorators.computed.collections import ComputedMixin
from forestadmin.datasource_toolkit.decorators.empty.collection import EmptyMixin
from forestadmin.datasource_toolkit.decorators.operators_replace.collections import OperatorReplaceMixin
from forestadmin.datasource_toolkit.decorators.proxy.collection import ProxyMixin
from forestadmin.datasource_toolkit.decorators.publication.collections import PublicationMixin
from forestadmin.datasource_toolkit.decorators.rename.collections import RenameMixin
from forestadmin.datasource_toolkit.decorators.schema.collection import SchemaMixin
from forestadmin.datasource_toolkit.decorators.search.collections import SearchMixin
from forestadmin.datasource_toolkit.decorators.segments.collections import SegmentMixin
from forestadmin.datasource_toolkit.decorators.validation.collection import ValidationMixin
from forestadmin.datasource_toolkit.interfaces.models.collections import CollectionSchema


class CustomizedCollection(
    EmptyMixin,
    ActionMixin,
    RenameMixin,
    ComputedMixin,
    ValidationMixin,
    OperatorReplaceMixin,
    SegmentMixin,
    PublicationMixin,
    SearchMixin,
    SchemaMixin,
    ProxyMixin,
):
    def __init__(self, *args: Any, **kwargs: Any):
        super(CustomizedCollection, self).__init__(*args, **kwargs)
        self._last_schema = None
        self._schema_refreshing = False

    def mark_schema_as_dirty(self):  # type: ignore
        super().mark_schema_as_dirty()
        self._last_schema = None
        self.child_collection._schema = self.schema  # type: ignore

    @property
    def schema(self) -> CollectionSchema:
        if not self._last_schema:
            self._last_schema = super().schema
        return self._last_schema

    def disableCount(self):
        self.override_schema("countable", False)
