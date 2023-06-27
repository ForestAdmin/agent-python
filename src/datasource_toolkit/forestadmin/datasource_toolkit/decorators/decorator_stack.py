from forestadmin.datasource_toolkit.decorators.action.collections import ActionCollectionDecorator
from forestadmin.datasource_toolkit.decorators.computed.collections import ComputedCollectionDecorator
from forestadmin.datasource_toolkit.decorators.datasource_decorator import DatasourceDecorator
from forestadmin.datasource_toolkit.decorators.empty.collection import EmptyCollectionDecorator
from forestadmin.datasource_toolkit.decorators.operators_equivalence.collections import (
    OperatorEquivalenceCollectionDecorator,
)
from forestadmin.datasource_toolkit.decorators.publication_field.collections import PublicationFieldCollectionDecorator
from forestadmin.datasource_toolkit.decorators.rename_field.collections import RenameFieldCollectionDecorator
from forestadmin.datasource_toolkit.decorators.schema.collection import SchemaCollectionDecorator
from forestadmin.datasource_toolkit.decorators.search.collections import SearchCollectionDecorator
from forestadmin.datasource_toolkit.decorators.segments.collections import SegmentCollectionDecorator
from forestadmin.datasource_toolkit.decorators.validation.collection import ValidationCollectionDecorator
from forestadmin.datasource_toolkit.interfaces.models.collections import Datasource


class DecoratorStack:
    def __init__(self, datasource: Datasource) -> None:
        last = datasource

        # Step 0: Do not query datasource when we know the result with yield an empty set.
        last = self.empty = DatasourceDecorator(last, EmptyCollectionDecorator)

        # Step 1: Computed-Relation-Computed sandwich (needed because some emulated relations depend
        # on computed fields, and some computed fields depend on relation...)
        # Note that replacement goes before emulation, as replacements may use emulated operators.
        last = self.early_computed = DatasourceDecorator(last, ComputedCollectionDecorator)
        # last = self.earlyOpEmulate = DatasourceDecorator(last, OperatorsEmulateCollection)
        last = self.early_op_equivalence = DatasourceDecorator(last, OperatorEquivalenceCollectionDecorator)
        # last = self.relation = DatasourceDecorator(last, RelationCollection)
        # last = self.late_computed = DatasourceDecorator(last, ComputedCollectionDecorator)
        # last = self.lateOpEmulate = DatasourceDecorator(last, OperatorsEmulateCollection)
        # last = self.late_op_equivalence = DatasourceDecorator(last, OperatorEquivalenceCollectionDecorator)

        # Step 2: Those need access to all fields. They can be loaded in any order.
        last = self.search = DatasourceDecorator(last, SearchCollectionDecorator)
        last = self.segment = DatasourceDecorator(last, SegmentCollectionDecorator)
        # last = self.sort = DatasourceDecorator(last, SortCollection)

        # Step 3: Access to all fields AND emulated capabilities
        # last = self.chart = ChartDataSourceDecorator(last)
        last = self.action = DatasourceDecorator(last, ActionCollectionDecorator)
        last = self.schema = DatasourceDecorator(last, SchemaCollectionDecorator)
        # last = self.write = WriteDataSourceDecorator(last)
        # last = self.hook = DatasourceDecorator(last, HookCollection)
        last = self.validation = DatasourceDecorator(last, ValidationCollectionDecorator)
        # last = self.binary = DatasourceDecorator(last, BinaryCollection)

        # Step 4: Renaming must be either the very first or very last so that naming in customer code is consistent.
        last = self.publication = DatasourceDecorator(last, PublicationFieldCollectionDecorator)
        last = self.rename_field = DatasourceDecorator(last, RenameFieldCollectionDecorator)

        self.datasource = last
