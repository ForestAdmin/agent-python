from unittest import TestCase
from unittest.mock import call, patch

from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.action.collections import ActionCollectionDecorator
from forestadmin.datasource_toolkit.decorators.computed.collections import ComputedCollectionDecorator
from forestadmin.datasource_toolkit.decorators.decorator_stack import DecoratorStack
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
        with patch(
            "forestadmin.datasource_toolkit.decorators.decorator_stack.DatasourceDecorator",
            return_value=self.datasource,
        ) as mocked_datasource_decorator:
            DecoratorStack(self.datasource)

            call_list = [
                call(self.datasource, EmptyCollectionDecorator),
                call(self.datasource, ComputedCollectionDecorator),
                call(self.datasource, OperatorEquivalenceCollectionDecorator),
                call(self.datasource, SearchCollectionDecorator),
                call(self.datasource, SegmentCollectionDecorator),
                call(self.datasource, ActionCollectionDecorator),
                call(self.datasource, SchemaCollectionDecorator),
                call(self.datasource, ValidationCollectionDecorator),
                call(self.datasource, PublicationFieldCollectionDecorator),
                call(self.datasource, RenameFieldCollectionDecorator),
            ]
            mocked_datasource_decorator.assert_has_calls(call_list)
