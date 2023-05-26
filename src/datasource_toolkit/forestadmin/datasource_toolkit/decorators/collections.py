from typing import Any

from forestadmin.datasource_toolkit.decorators.action.collections import ActionMixin
from forestadmin.datasource_toolkit.decorators.computed.collections import ComputedMixin
from forestadmin.datasource_toolkit.decorators.empty.collection import EmptyMixin
from forestadmin.datasource_toolkit.decorators.operators_replace.collections import OperatorReplaceMixin
from forestadmin.datasource_toolkit.decorators.proxy.collection import ProxyMixin
from forestadmin.datasource_toolkit.decorators.publication.collections import PublicationMixin
from forestadmin.datasource_toolkit.decorators.rename.collections import RenameMixin
from forestadmin.datasource_toolkit.decorators.search.collections import SearchMixin
from forestadmin.datasource_toolkit.decorators.segments.collections import SegmentMixin
from forestadmin.datasource_toolkit.interfaces.models.collections import CollectionSchema


class CustomizedCollection(
    EmptyMixin,
    ActionMixin,
    RenameMixin,
    ComputedMixin,
    OperatorReplaceMixin,
    SegmentMixin,
    PublicationMixin,
    SearchMixin,
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


# export default class DecoratorsStack {
#   action: DataSourceDecorator<ActionCollectionDecorator>;
#   chart: ChartDataSourceDecorator;
#   earlyComputed: DataSourceDecorator<ComputedCollectionDecorator>;
#   earlyOpEmulate: DataSourceDecorator<OperatorsEmulateCollectionDecorator>;
#   relation: DataSourceDecorator<RelationCollectionDecorator>;
#   lateComputed: DataSourceDecorator<ComputedCollectionDecorator>;
#   lateOpEmulate: DataSourceDecorator<OperatorsEmulateCollectionDecorator>;
#   publication: DataSourceDecorator<PublicationFieldCollectionDecorator>;
#   renameField: DataSourceDecorator<RenameFieldCollectionDecorator>;
#   schema: DataSourceDecorator<SchemaCollectionDecorator>;
#   search: DataSourceDecorator<SearchCollectionDecorator>;
#   segment: DataSourceDecorator<SegmentCollectionDecorator>;
#   sortEmulate: DataSourceDecorator<SortEmulateCollectionDecorator>;
#   validation: DataSourceDecorator<ValidationCollectionDecorator>;
#   write: WriteDataSourceDecorator;
#   hook: DataSourceDecorator<HookCollectionDecorator>;
#   dataSource: DataSource;

#   private customizations: Array<(logger: Logger) => Promise<void>> = [];

#   constructor(dataSource: DataSource) {
#     let last: DataSource = dataSource;

#     /* eslint-disable no-multi-assign */
#     // Step 0: Do not query datasource when we know the result with yield an empty set.
#     last = new DataSourceDecorator(last, EmptyCollectionDecorator);
#     last = new DataSourceDecorator(last, OperatorsEquivalenceCollectionDecorator);

#     // Step 1: Computed-Relation-Computed sandwich (needed because some emulated relations depend
#     // on computed fields, and some computed fields depend on relation...)
#     // Note that replacement goes before emulation, as replacements may use emulated operators.
#     last = this.earlyComputed = new DataSourceDecorator(last, ComputedCollectionDecorator);
#     last = this.earlyOpEmulate = new DataSourceDecorator(last, OperatorsEmulateCollectionDecorator);
#     last = new DataSourceDecorator(last, OperatorsEquivalenceCollectionDecorator);
#     last = this.relation = new DataSourceDecorator(last, RelationCollectionDecorator);
#     last = this.lateComputed = new DataSourceDecorator(last, ComputedCollectionDecorator);
#     last = this.lateOpEmulate = new DataSourceDecorator(last, OperatorsEmulateCollectionDecorator);
#     last = new DataSourceDecorator(last, OperatorsEquivalenceCollectionDecorator);

#     // Step 2: Those need access to all fields. They can be loaded in any order.
#     last = this.search = new DataSourceDecorator(last, SearchCollectionDecorator);
#     last = this.segment = new DataSourceDecorator(last, SegmentCollectionDecorator);
#     last = this.sortEmulate = new DataSourceDecorator(last, SortEmulateCollectionDecorator);

#     // Step 3: Access to all fields AND emulated capabilities
#     last = this.chart = new ChartDataSourceDecorator(last);
#     last = this.action = new DataSourceDecorator(last, ActionCollectionDecorator);
#     last = this.schema = new DataSourceDecorator(last, SchemaCollectionDecorator);
#     last = this.write = new WriteDataSourceDecorator(last);
#     last = this.hook = new DataSourceDecorator(last, HookCollectionDecorator);
#     last = this.validation = new DataSourceDecorator(last, ValidationCollectionDecorator);

#     // Step 4: Renaming must be either the very first or very last so that naming in customer code
#     // is consistent.
#     last = this.publication = new DataSourceDecorator(last, PublicationFieldCollectionDecorator);
#     last = this.renameField = new DataSourceDecorator(last, RenameFieldCollectionDecorator);
#     /* eslint-enable no-multi-assign */

#     this.dataSource = last;
#   }
