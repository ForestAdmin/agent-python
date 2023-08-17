from unittest import TestCase
from unittest.mock import call, patch

from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.action.collections import ActionCollectionDecorator
from forestadmin.datasource_toolkit.decorators.computed.collections import ComputedCollectionDecorator
from forestadmin.datasource_toolkit.decorators.decorator_stack import DecoratorStack
from forestadmin.datasource_toolkit.decorators.empty.collection import EmptyCollectionDecorator
from forestadmin.datasource_toolkit.decorators.hook.collections import CollectionHookDecorator
from forestadmin.datasource_toolkit.decorators.operators_emulate.collections import OperatorsEmulateCollectionDecorator
from forestadmin.datasource_toolkit.decorators.operators_equivalence.collections import (
    OperatorEquivalenceCollectionDecorator,
)
from forestadmin.datasource_toolkit.decorators.publication_field.collections import PublicationFieldCollectionDecorator
from forestadmin.datasource_toolkit.decorators.relation.collections import RelationCollectionDecorator
from forestadmin.datasource_toolkit.decorators.rename_field.collections import RenameFieldCollectionDecorator
from forestadmin.datasource_toolkit.decorators.schema.collection import SchemaCollectionDecorator
from forestadmin.datasource_toolkit.decorators.search.collections import SearchCollectionDecorator
from forestadmin.datasource_toolkit.decorators.segments.collections import SegmentCollectionDecorator
from forestadmin.datasource_toolkit.decorators.sort_emulate.collections import SortCollectionDecorator
from forestadmin.datasource_toolkit.decorators.validation.collection import ValidationCollectionDecorator
from forestadmin.datasource_toolkit.interfaces.fields import Column, FieldType, PrimitiveType


class TestDecoratorStack(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.datasource: Datasource = Datasource()

        Collection.__abstractmethods__ = set()  # to instantiate abstract class
        cls.collection_product = Collection("Product", cls.datasource)
        cls.collection_product.add_fields(
            {
                "id": Column(column_type=PrimitiveType.NUMBER, is_primary_key=True, type=FieldType.COLUMN),
                "name": Column(column_type=PrimitiveType.STRING, type=FieldType.COLUMN),
                "price": Column(
                    column_type=PrimitiveType.NUMBER,
                    type=FieldType.COLUMN,
                ),
            }
        )
        cls.datasource.add_collection(cls.collection_product)

    def test_creation_instantiate_all_decorator_with_datasource_decorator(self):
        # mock for datasource decorator
        datasource_decorators_to_patch = [
            # (datasource_name, [arguments for call with])
            ("ChartDataSourceDecorator", [self.datasource]),
            ("WriteDataSourceDecorator", [self.datasource]),
        ]
        patched_datasource_decorators = []
        for datasource_decorator, arg_list_expected in datasource_decorators_to_patch:
            patcher = patch(
                f"forestadmin.datasource_toolkit.decorators.decorator_stack.{datasource_decorator}",
                return_value=self.datasource,
            )
            mock = patcher.start()

            patched_datasource_decorators.append((patcher, mock, arg_list_expected))

        # collection decorators
        with patch(
            "forestadmin.datasource_toolkit.decorators.decorator_stack.DatasourceDecorator",
            return_value=self.datasource,
        ) as mocked_datasource_decorator:
            DecoratorStack(self.datasource)

            call_list = [
                call(self.datasource, EmptyCollectionDecorator),
                call(self.datasource, ComputedCollectionDecorator),
                call(self.datasource, OperatorsEmulateCollectionDecorator),
                call(self.datasource, OperatorEquivalenceCollectionDecorator),
                call(self.datasource, RelationCollectionDecorator),
                call(self.datasource, ComputedCollectionDecorator),
                call(self.datasource, OperatorsEmulateCollectionDecorator),
                call(self.datasource, OperatorEquivalenceCollectionDecorator),
                call(self.datasource, SearchCollectionDecorator),
                call(self.datasource, SegmentCollectionDecorator),
                call(self.datasource, SortCollectionDecorator),
                # call(self.datasource, ChartCollectionDecorator),
                call(self.datasource, ActionCollectionDecorator),
                call(self.datasource, SchemaCollectionDecorator),
                # call(self.datasource, WriteDataSourceDecorator),
                call(self.datasource, CollectionHookDecorator),
                call(self.datasource, ValidationCollectionDecorator),
                call(self.datasource, PublicationFieldCollectionDecorator),
                call(self.datasource, RenameFieldCollectionDecorator),
            ]
            mocked_datasource_decorator.assert_has_calls(call_list)

        for patcher, mocked, arg_list_expected in patched_datasource_decorators:
            mocked.assert_called_once_with(*arg_list_expected)
            patcher.stop()
