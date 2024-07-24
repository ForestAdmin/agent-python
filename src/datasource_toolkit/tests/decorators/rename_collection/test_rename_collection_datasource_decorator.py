import asyncio
import sys
from unittest import TestCase

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.rename_collection.collection import RenameCollectionCollectionDecorator
from forestadmin.datasource_toolkit.decorators.rename_collection.datasource import RenameCollectionDataSourceDecorator
from forestadmin.datasource_toolkit.exceptions import ForestException
from forestadmin.datasource_toolkit.interfaces.fields import (
    Column,
    FieldType,
    ManyToOne,
    OneToOne,
    Operator,
    PolymorphicManyToOne,
    PolymorphicOneToMany,
    PolymorphicOneToOne,
    PrimitiveType,
)


class TestRenameCollectionDatasourceDecorator(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()
        cls.datasource: Datasource = Datasource()
        Collection.__abstractmethods__ = set()  # to instantiate abstract class

        cls.collection_book = Collection("Book", cls.datasource)
        cls.collection_book.add_fields(
            {
                "id": Column(column_type=PrimitiveType.NUMBER, is_primary_key=True, type=FieldType.COLUMN),
                "title": Column(
                    column_type=PrimitiveType.STRING,
                    filter_operators=[Operator.LONGER_THAN, Operator.PRESENT],
                    type=FieldType.COLUMN,
                ),
                "author_id": Column(column_type=PrimitiveType.NUMBER, type=FieldType.COLUMN),
                "author": ManyToOne(
                    foreign_collection="Person",
                    foreign_key="author_id",
                    foreign_key_target="id",
                    type=FieldType.MANY_TO_ONE,
                ),
            }
        )

        cls.collection_person = Collection("Person", cls.datasource)
        cls.collection_person.add_fields(
            {
                "id": Column(column_type=PrimitiveType.NUMBER, is_primary_key=True, type=FieldType.COLUMN),
                "book": OneToOne(
                    origin_key="author_id", origin_key_target="id", foreign_collection="Book", type=FieldType.ONE_TO_ONE
                ),
                "first_name": Column(column_type=PrimitiveType.STRING, type=FieldType.COLUMN),
            }
        )
        cls.collection_rating = Collection("Rating", cls.datasource)
        cls.collection_rating.add_fields(
            {
                "id": Column(column_type=PrimitiveType.NUMBER, is_primary_key=True, type=FieldType.COLUMN),
                "rating": Column(column_type=PrimitiveType.NUMBER, type=FieldType.COLUMN),
                "target_id": Column(column_type=PrimitiveType.NUMBER, type=FieldType.COLUMN),
                "target_type": Column(column_type=PrimitiveType.STRING, type=FieldType.COLUMN),
                "target": PolymorphicManyToOne(
                    foreign_collections=["Bar", "Restaurant"],
                    foreign_key="target_id",
                    foreign_key_targets={"Bar": "id", "Restaurant": "id"},
                    foreign_key_type_field="target_type",
                    type=FieldType.POLYMORPHIC_MANY_TO_ONE,
                ),
            }
        )
        cls.collection_bar = Collection("Bar", cls.datasource)
        cls.collection_bar.add_fields(
            {
                "id": Column(column_type=PrimitiveType.NUMBER, is_primary_key=True, type=FieldType.COLUMN),
                "name": Column(column_type=PrimitiveType.NUMBER, type=FieldType.COLUMN),
                "ratings": PolymorphicOneToMany(
                    foreign_collection="Rating",
                    origin_key="target_id",
                    origin_key_target="id",
                    origin_type_field="target_type",
                    origin_type_value="Bar",
                    type=FieldType.POLYMORPHIC_ONE_TO_MANY,
                ),
            }
        )
        cls.collection_restaurant = Collection("Restaurant", cls.datasource)
        cls.collection_restaurant.add_fields(
            {
                "id": Column(column_type=PrimitiveType.NUMBER, is_primary_key=True, type=FieldType.COLUMN),
                "name": Column(column_type=PrimitiveType.NUMBER, type=FieldType.COLUMN),
                "ratings": PolymorphicOneToOne(
                    foreign_collection="Rating",
                    origin_key="target_id",
                    origin_key_target="id",
                    origin_type_field="target_type",
                    origin_type_value="Restaurant",
                    type=FieldType.POLYMORPHIC_ONE_TO_ONE,
                ),
            }
        )

        cls.datasource.add_collection(cls.collection_book)
        cls.datasource.add_collection(cls.collection_person)
        cls.datasource.add_collection(cls.collection_rating)
        cls.datasource.add_collection(cls.collection_bar)
        cls.datasource.add_collection(cls.collection_restaurant)

        cls.mocked_caller = User(
            rendering_id=1,
            user_id=1,
            tags={},
            email="dummy@user.fr",
            first_name="dummy",
            last_name="user",
            team="operational",
            timezone=zoneinfo.ZoneInfo("Europe/Paris"),
        )

    def setUp(self) -> None:
        self.decorated_datasource = RenameCollectionDataSourceDecorator(self.datasource)

    def test_should_return_real_name_when_not_renamed(self):
        self.assertEqual(self.decorated_datasource.get_collection("Person").name, "Person")

    def test_should_rename_a_collection(self):
        self.decorated_datasource.rename_collections({"Person": "User"})

        self.assertRaisesRegex(
            ForestException,
            r"🌳🌳🌳Collection 'Person' has been renamed to 'User'",
            self.decorated_datasource.get_collection,
            "Person",
        )
        self.assertIsInstance(self.decorated_datasource.get_collection("User"), RenameCollectionCollectionDecorator)

    def test_rename_collection_should_throw_if_name_already_use(self):
        self.assertRaisesRegex(
            ForestException,
            r"🌳🌳🌳The given new collection name Book is already defined in the dataSource",
            self.decorated_datasource.rename_collections,
            {"Person": "Book"},
        )

    def test_rename_collection_should_throw_if_old_name_does_not_exists(self):
        self.assertRaisesRegex(
            ForestException,
            r"🌳🌳🌳Collection 'Foo' not found",
            self.decorated_datasource.rename_collections,
            {"Foo": "Bar"},
        )

    def test_rename_collection_should_throw_if_called_twice_on_same_collection(self):
        self.decorated_datasource.rename_collections({"Person": "User"})
        self.assertRaisesRegex(
            ForestException,
            r"🌳🌳🌳Cannot rename a collection twice: Person->User->User2",
            self.decorated_datasource.rename_collections,
            {"User": "User2"},
        )

    def test_rename_collection_should_throw_if_try_to_rename_a_collection_which_is_target_of_polymorphic_relation(self):
        self.assertRaisesRegex(
            ForestException,
            r"🌳🌳🌳Cannot rename collection Bar because it's a target of a polymorphic relation 'Rating.target'",
            self.decorated_datasource.rename_collections,
            {"Bar": "Whatever"},
        )

        self.assertRaisesRegex(
            ForestException,
            r"🌳🌳🌳Cannot rename collection Restaurant because it's a target of a polymorphic relation 'Rating.target'",
            self.decorated_datasource.rename_collections,
            {"Restaurant": "Whatever"},
        )

    def test_rename_collection_should_rename_a_collection_owning_a_polymorphic_many_to_one(self):
        self.decorated_datasource.rename_collections({"Rating": "Whatever"})
        self.assertIsInstance(self.decorated_datasource.get_collection("Whatever"), RenameCollectionCollectionDecorator)
