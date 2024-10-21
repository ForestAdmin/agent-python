import asyncio
import sys
from unittest import TestCase

from forestadmin.datasource_toolkit.datasource_customizer.datasource_customizer import DatasourceCustomizer
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.interfaces.fields import (
    Column,
    FieldType,
    ManyToOne,
    OneToOne,
    Operator,
    PrimitiveType,
)
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter


class TestComputedCollectionDecorator(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()
        cls.datasource: Datasource = Datasource()

        Collection.__abstractmethods__ = set()  # to instantiate abstract class
        cls.collection_book = Collection("Book", cls.datasource)
        cls.collection_book.add_fields(
            {
                "id": Column(
                    column_type=PrimitiveType.NUMBER,
                    is_primary_key=True,
                    type=FieldType.COLUMN,
                    filter_operators={Operator.EQUAL, Operator.IN},
                ),
                "author_id": Column(column_type=PrimitiveType.STRING, type=FieldType.COLUMN),
                "author": ManyToOne(
                    foreign_collection="Person",
                    foreign_key="author_id",
                    foreign_key_target="id",
                    type=FieldType.MANY_TO_ONE,
                ),
                "title": Column(
                    column_type=PrimitiveType.STRING,
                    type=FieldType.COLUMN,
                ),
                "sub_title": Column(column_type=PrimitiveType.STRING, type=FieldType.COLUMN),
            }
        )
        cls.collection_person = Collection("Person", cls.datasource)
        cls.collection_person.add_fields(
            {
                "id": Column(
                    column_type=PrimitiveType.NUMBER,
                    is_primary_key=True,
                    type=FieldType.COLUMN,
                    filter_operators={Operator.EQUAL, Operator.IN},
                ),
                "first_name": Column(
                    column_type=PrimitiveType.STRING,
                    type=FieldType.COLUMN,
                    filter_operators={Operator.CONTAINS, Operator.ENDS_WITH, Operator.EQUAL, Operator.LIKE},
                ),
                "last_name": Column(column_type=PrimitiveType.STRING, type=FieldType.COLUMN),
                "book": OneToOne(
                    origin_key="author_id", origin_key_target="id", foreign_collection="Book", type=FieldType.ONE_TO_ONE
                ),
            }
        )
        cls.mocked_caller = User(
            rendering_id=1,
            user_id=1,
            tags={},
            email="dummy@user.fr",
            first_name="dummy",
            last_name="user",
            team="operational",
            timezone=zoneinfo.ZoneInfo("Europe/Paris"),
            request={"ip": "127.0.0.1"},
        )

    def setUp(self) -> None:
        self.datasource.add_collection(self.collection_book)
        self.datasource.add_collection(self.collection_person)

        self.datasource_customizer: DatasourceCustomizer = DatasourceCustomizer()
        self.datasource_customizer.add_datasource(self.datasource, {})

    def test_operators_should_correctly_be_replaced(self):
        book_collection_customizer = self.datasource_customizer.customize_collection("Book")
        book_collection_customizer.import_field("author_first_name", {"path": "author:first_name"})
        self.loop.run_until_complete(self.datasource_customizer.stack.apply_queue_customization())

        for operator in [Operator.CONTAINS, Operator.ENDS_WITH, Operator.EQUAL, Operator.LIKE]:
            new_filter = self.loop.run_until_complete(
                self.datasource_customizer.stack.early_op_emulate.get_collection("Book")._refine_filter(
                    self.mocked_caller,
                    Filter({"condition_tree": ConditionTreeLeaf("author_first_name", operator, "test")}),
                )
            )
            self.assertEqual(new_filter.condition_tree.field, "author:first_name")
            self.assertEqual(new_filter.condition_tree.operator, operator)
