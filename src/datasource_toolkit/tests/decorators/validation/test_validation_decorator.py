import asyncio
import sys
from unittest import TestCase
from unittest.mock import patch

if sys.version_info >= (3, 8):
    from unittest.mock import AsyncMock
else:
    from mock import AsyncMock

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.datasource_decorator import DatasourceDecorator
from forestadmin.datasource_toolkit.decorators.validation.collection import ValidationCollectionDecorator
from forestadmin.datasource_toolkit.exceptions import (
    DatasourceToolkitException,
    ForestException,
    ForestValidationException,
)
from forestadmin.datasource_toolkit.interfaces.fields import (
    Column,
    FieldType,
    ManyToOne,
    OneToOne,
    Operator,
    PrimitiveType,
)
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter, FilterComponent


class TesValidationCollectionDecorator(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()
        cls.datasource: Datasource = Datasource()

        Collection.__abstractmethods__ = set()  # to instantiate abstract class
        cls.collection_book = Collection("Book", cls.datasource)
        cls.collection_book.add_fields(
            {
                "id": Column(
                    column_type=PrimitiveType.NUMBER, is_primary_key=True, is_read_only=True, type=FieldType.COLUMN
                ),
                "author_id": Column(column_type=PrimitiveType.STRING, is_read_only=True, type=FieldType.COLUMN),
                "author": ManyToOne(
                    foreign_collection="Person",
                    foreign_key="author_id",
                    foreign_key_target="id",
                    type=FieldType.MANY_TO_ONE,
                ),
                "title": Column(
                    column_type=PrimitiveType.STRING,
                    filter_operators=[Operator.LONGER_THAN, Operator.PRESENT],
                    type=FieldType.COLUMN,
                ),
                "sub_title": Column(
                    column_type=PrimitiveType.STRING, filter_operators=[Operator.LONGER_THAN], type=FieldType.COLUMN
                ),
            }
        )
        cls.collection_person = Collection("Person", cls.datasource)
        cls.collection_person.add_fields(
            {
                "id": Column(column_type=PrimitiveType.NUMBER, is_primary_key=True, type=FieldType.COLUMN),
                "first_name": Column(column_type=PrimitiveType.STRING, type=FieldType.COLUMN),
                "last_name": Column(column_type=PrimitiveType.STRING, type=FieldType.COLUMN),
                "book": OneToOne(origin_key="author_id", origin_key_target="id", foreign_collection="Book"),
            }
        )
        cls.datasource.add_collection(cls.collection_book)
        cls.datasource.add_collection(cls.collection_person)

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
        cls.datasource_decorator = DatasourceDecorator(cls.datasource, ValidationCollectionDecorator)

    def test_add_validation_errors(self):
        decorated_collection_book = self.datasource_decorator.get_collection("Book")
        # on nonexisting field
        self.assertRaisesRegex(
            DatasourceToolkitException,
            r"🌳🌳🌳Column not found: Book.__dont_exists",
            decorated_collection_book.add_validation,
            "__dont_exists",
            {"operator": Operator.PRESENT},
        )

        # on a relation
        self.assertRaisesRegex(
            DatasourceToolkitException,
            r"🌳🌳🌳Unexpected field type: Book.author \(found FieldType.MANY_TO_ONE expected Column\)",
            decorated_collection_book.add_validation,
            "author",
            {"operator": Operator.PRESENT},
        )

        # on readonly field
        self.assertRaisesRegex(
            ForestException,
            r"🌳🌳🌳Cannot add validators on a readonly field",
            decorated_collection_book.add_validation,
            "id",
            {"operator": Operator.PRESENT},
        )

    def test_add_validation(self):
        decorated_collection_book = self.datasource_decorator.get_collection("Book")
        decorated_collection_book.add_validation("title", {"operator": Operator.LONGER_THAN, "value": 5})
        assert len(decorated_collection_book.validations["title"]) == 1

    def test_creation_validation(self):
        decorated_collection_book = self.datasource_decorator.get_collection("Book")
        decorated_collection_book.add_validation("title", {"operator": Operator.LONGER_THAN, "value": 5})
        decorated_collection_book.add_validation("sub_title", {"operator": Operator.LONGER_THAN, "value": 5})

        self.assertRaisesRegex(
            ForestValidationException,
            r"🌳🌳🌳sub_title failed validation rule: 'longer_than\(5\)'",
            self.loop.run_until_complete,
            decorated_collection_book.create(
                self.mocked_caller,
                [{"title": "long_title", "sub_title": ""}],
            ),
        )

        self.assertRaisesRegex(
            ForestValidationException,
            r"🌳🌳🌳title failed validation rule: 'longer_than\(5\)'",
            self.loop.run_until_complete,
            decorated_collection_book.create(
                self.mocked_caller,
                [{"title": "", "sub_title": "long subtitle"}],
            ),
        )
        with patch.object(self.collection_book, "create", new_callable=AsyncMock) as mocked_create:
            self.loop.run_until_complete(
                decorated_collection_book.create(
                    self.mocked_caller,
                    [{"title": "long title", "sub_title": "long subtitle"}],
                )
            )
            mocked_create.assert_awaited_once_with(
                self.mocked_caller, [{"title": "long title", "sub_title": "long subtitle"}]
            )

        decorated_collection_book.add_validation("title", {"operator": Operator.PRESENT})
        self.assertRaisesRegex(
            ForestValidationException,
            r"🌳🌳🌳title failed validation rule: 'present'",
            self.loop.run_until_complete,
            decorated_collection_book.create(
                self.mocked_caller,
                [{"sub_title": "long subtitle"}],
            ),
        )

    def test_update_validation(self):
        decorated_collection_book = self.datasource_decorator.get_collection("Book")
        decorated_collection_book.add_validation("title", {"operator": Operator.LONGER_THAN, "value": 5})
        decorated_collection_book.add_validation("sub_title", {"operator": Operator.LONGER_THAN, "value": 5})

        self.assertRaisesRegex(
            ForestValidationException,
            r"🌳🌳🌳sub_title failed validation rule: 'longer_than\(5\)'",
            self.loop.run_until_complete,
            decorated_collection_book.update(
                self.mocked_caller,
                Filter(FilterComponent()),
                {"sub_title": "1"},
            ),
        )

        with patch.object(self.collection_book, "update", new_callable=AsyncMock) as mocked_update:
            self.loop.run_until_complete(
                decorated_collection_book.update(
                    self.mocked_caller,
                    Filter(FilterComponent()),
                    {"sub_title": "long subtitle"},
                )
            )
            mocked_update.assert_awaited_once_with(
                self.mocked_caller, Filter(FilterComponent()), {"sub_title": "long subtitle"}
            )

        decorated_collection_book.add_validation("title", {"operator": Operator.PRESENT})
        self.assertRaisesRegex(
            ForestValidationException,
            r"🌳🌳🌳title failed validation rule: 'present'",
            self.loop.run_until_complete,
            decorated_collection_book.update(
                self.mocked_caller,
                Filter(FilterComponent()),
                {"title": None},
            ),
        )

    def test_allow_null_with_other_validation(self):
        decorated_collection_book = self.datasource_decorator.get_collection("Book")
        decorated_collection_book.add_validation("title", {"operator": Operator.LONGER_THAN, "value": 5})

        with patch.object(self.collection_book, "create", new_callable=AsyncMock) as mocked_create:
            self.loop.run_until_complete(
                decorated_collection_book.create(
                    self.mocked_caller,
                    [{"title": None, "sub_title": "long subtitle"}],
                )
            )
            mocked_create.assert_awaited_once_with(self.mocked_caller, [{"title": None, "sub_title": "long subtitle"}])

        with patch.object(self.collection_book, "update", new_callable=AsyncMock) as mocked_update:
            self.loop.run_until_complete(
                decorated_collection_book.update(
                    self.mocked_caller,
                    Filter(FilterComponent()),
                    {"title": None, "sub_title": "long subtitle"},
                )
            )
            mocked_update.assert_awaited_once_with(
                self.mocked_caller, Filter(FilterComponent()), {"title": None, "sub_title": "long subtitle"}
            )
