from unittest import TestCase

from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.interfaces.fields import Column, FieldType, ManyToOne, OneToMany, PrimitiveType
from forestadmin.datasource_toolkit.utils.collections import CollectionUtils, CollectionUtilsException


class CollectionUtilTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # cls.loop = asyncio.new_event_loop()
        cls.datasource: Datasource = Datasource()

        Collection.__abstractmethods__ = set()  # to instantiate abstract class
        cls.collection_book = Collection("Book", cls.datasource)
        cls.collection_book.add_fields(
            {
                "id": Column(column_type=PrimitiveType.NUMBER, is_primary_key=True, type=FieldType.COLUMN),
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
                "cover_id": {
                    "column_type": PrimitiveType.NUMBER,
                    "type": FieldType.COLUMN,
                    "filter_operators": set(),
                    "default_value": None,
                    "enum_values": None,
                    "is_primary_key": None,
                    "is_read_only": None,
                    "is_sortable": None,
                    "validations": None,
                },
                "cover": {
                    "type": FieldType.MANY_TO_ONE,
                    "foreign_key": "cover_id",
                    "foreign_key_target": "id",
                    "foreign_collection": "Cover",
                },
                "comments": {
                    "type": FieldType.POLYMORPHIC_ONE_TO_MANY,
                    "foreign_collection": "Comment",
                    "origin_key": "commentable_id",
                    "origin_key_target": "id",
                    "origin_type_field": "commentable_type",
                    "origin_type_value": "Book",
                },
            }
        )
        cls.collection_cover = Collection("Cover", cls.datasource)
        cls.collection_cover.add_fields(
            {
                "id": Column(column_type=PrimitiveType.NUMBER, is_primary_key=True, type=FieldType.COLUMN),
                "book": {
                    "type": FieldType.ONE_TO_ONE,
                    "origin_key": "cover_id",
                    "origin_key_target": "id",
                    "foreign_collection": "Book",
                },
                "comments": {
                    "type": FieldType.POLYMORPHIC_ONE_TO_MANY,
                    "foreign_collection": "Comment",
                    "origin_key": "commentable_id",
                    "origin_key_target": "id",
                    "origin_type_field": "commentable_type",
                    "origin_type_value": "Cover",
                },
            }
        )
        cls.collection_person = Collection("Person", cls.datasource)
        cls.collection_person.add_fields(
            {
                "id": Column(column_type=PrimitiveType.NUMBER, is_primary_key=True, type=FieldType.COLUMN),
                "first_name": Column(column_type=PrimitiveType.STRING, type=FieldType.COLUMN),
                "last_name": Column(column_type=PrimitiveType.STRING, type=FieldType.COLUMN),
                "book": OneToMany(
                    origin_key="author_id",
                    origin_key_target="id",
                    foreign_collection="Book",
                    type=FieldType.ONE_TO_MANY,
                ),
                "comments": {
                    "type": FieldType.POLYMORPHIC_ONE_TO_ONE,
                    "foreign_collection": "Comment",
                    "origin_key": "commentable_id",
                    "origin_key_target": "id",
                    "origin_type_field": "commentable_type",
                    "origin_type_value": "Person",
                },
            }
        )
        cls.collection_comment = Collection("Comment", cls.datasource)
        cls.collection_comment.add_fields(
            {
                "id": Column(column_type=PrimitiveType.NUMBER, is_primary_key=True, type=FieldType.COLUMN),
                "comment": Column(column_type=PrimitiveType.STRING, type=FieldType.COLUMN),
                "commentable_id": Column(column_type=PrimitiveType.NUMBER, type=FieldType.COLUMN),
                "commentable_type": Column(
                    column_type=PrimitiveType.STRING,
                    type=FieldType.COLUMN,
                    enum_values=["Book", "Person", "Cover"],
                ),
                "commentable": {
                    "type": FieldType.POLYMORPHIC_MANY_TO_ONE,
                    "foreign_collections": ["Book", "Person", "Cover"],
                    "foreign_key": "commentable_id",
                    "foreign_key_type_field": "commentable_type",
                    "foreign_key_targets": {
                        "Book": "id",
                        "Person": "id",
                        "Cover": "id",
                    },
                },
            }
        )
        cls.datasource.add_collection(cls.collection_book)
        cls.datasource.add_collection(cls.collection_cover)
        cls.datasource.add_collection(cls.collection_person)
        cls.datasource.add_collection(cls.collection_comment)
        return super().setUpClass()


class CollectionUtilGetFieldSchema(CollectionUtilTest):
    def test_should_return_correct_field(self):
        self.assertEqual(
            CollectionUtils.get_field_schema(self.collection_book, "cover_id"),
            self.collection_book.get_field("cover_id"),
        )

        self.assertEqual(
            CollectionUtils.get_field_schema(self.collection_book, "cover:book"),
            self.collection_cover.get_field("book"),
        )

        self.assertEqual(
            CollectionUtils.get_field_schema(self.collection_cover, "book:author:last_name"),
            self.collection_person.get_field("last_name"),
        )

    def test_should_raise_when_path_dont_exists(self):
        self.assertRaisesRegex(
            CollectionUtilsException,
            r"Column not found Book.bla. Fields are .*",
            CollectionUtils.get_field_schema,
            self.collection_book,
            "bla",
        )


class CollectionUtilGetInverseRelation(CollectionUtilTest):
    def test_should_raise_on_polymorphic_many_to_one(self):
        self.assertRaisesRegex(
            CollectionUtilsException,
            r"A polymorphic many to one \(Comment.commentable\) have many reverse relations",
            CollectionUtils.get_inverse_relation,
            self.collection_comment,
            "commentable",
        )

    def test_should_work_over_polymorphic_one_to_one(self):
        self.assertEqual(CollectionUtils.get_inverse_relation(self.collection_person, "comments"), "commentable")

    def test_should_work_over_polymorphic_one_to_many(self):
        self.assertEqual(CollectionUtils.get_inverse_relation(self.collection_book, "comments"), "commentable")
