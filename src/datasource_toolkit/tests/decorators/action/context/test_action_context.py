import asyncio
import sys
from unittest import TestCase
from unittest.mock import AsyncMock, patch

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.action.collections import ActionCollectionDecorator
from forestadmin.datasource_toolkit.decorators.action.context.base import ActionContext
from forestadmin.datasource_toolkit.decorators.action.context.bulk import ActionContextBulk
from forestadmin.datasource_toolkit.decorators.action.context.single import ActionContextSingle
from forestadmin.datasource_toolkit.decorators.datasource_decorator import DatasourceDecorator
from forestadmin.datasource_toolkit.interfaces.fields import Column, FieldType, PrimitiveType
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection


class BaseTestActionContext(TestCase):
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
                    type=FieldType.COLUMN,
                ),
            }
        )
        cls.datasource.add_collection(cls.collection_book)

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

        cls.records = [{"id": 1, "title": "Foundation"}, {"id": 2, "title": "Beat the dealer"}]

    def setUp(self) -> None:
        self.datasource_decorator = DatasourceDecorator(self.datasource, ActionCollectionDecorator)
        self.decorated_collection = self.datasource_decorator.get_collection("Book")


class TestActionContext(BaseTestActionContext):
    def test_form_value_should_return_correct_value(self):
        context = ActionContext(
            self.decorated_collection, self.mocked_caller, {"title": "Foundation"}, PaginatedFilter({})
        )
        assert context.form_values.get("title") == "Foundation"
        assert "title" in context.form_values
        assert context.form_values["title"] == "Foundation"

    def test_form_value_should_return_null_when_key_is_missing(self):
        context = ActionContext(
            self.decorated_collection, self.mocked_caller, {"title": "Foundation"}, PaginatedFilter({})
        )
        assert context.form_values.get("foo") is None

    def test_get_records_should_return_values_of_list_collection(self):
        context = ActionContext(
            self.decorated_collection, self.mocked_caller, {"title": "Foundation"}, PaginatedFilter({})
        )

        with patch.object(self.collection_book, "list", new_callable=AsyncMock, return_value=self.records):
            records = self.loop.run_until_complete(context.get_records(Projection("id", "title")))

        assert records == self.records


class TestActionContextSingle(BaseTestActionContext):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.record = {"id": 1, "title": "Foundation"}

    def test_get_record_id_should_return_corresponding_id(self):
        context = ActionContextSingle(
            self.decorated_collection, self.mocked_caller, {"title": "Foundation"}, PaginatedFilter({})
        )
        with patch.object(self.collection_book, "list", new_callable=AsyncMock, return_value=[self.record]):
            record_id = self.loop.run_until_complete(context.get_record_id())
        assert record_id == 1

    def test_get_record_id_should_return_null_if_no_corresponding_id(self):
        context = ActionContextSingle(
            self.decorated_collection, self.mocked_caller, {"title": "Foundation"}, PaginatedFilter({})
        )

        with patch.object(self.collection_book, "list", new_callable=AsyncMock, return_value=[]):
            record_id = self.loop.run_until_complete(context.get_record_id())
        assert record_id is None

    def test_get_record_should_return_the_record(self):
        context = ActionContextSingle(
            self.decorated_collection, self.mocked_caller, {"title": "Foundation"}, PaginatedFilter({})
        )

        with patch.object(self.collection_book, "list", new_callable=AsyncMock, return_value=[self.record]):
            record = self.loop.run_until_complete(context.get_record(Projection("id", "title")))
        assert record == self.record

    def test_get_record_should_return_null_if_no_record_the_record(self):
        context = ActionContextSingle(
            self.decorated_collection, self.mocked_caller, {"title": "Foundation"}, PaginatedFilter({})
        )

        with patch.object(self.collection_book, "list", new_callable=AsyncMock, return_value=[]):
            record = self.loop.run_until_complete(context.get_record(Projection("id", "title")))
        assert record is None


class TestActionContextBulk(BaseTestActionContext):
    def test_get_records_ids_should_return_corresponding_id(self):
        context = ActionContextBulk(
            self.decorated_collection, self.mocked_caller, {"title": "Foundation"}, PaginatedFilter({})
        )

        with patch.object(self.collection_book, "list", new_callable=AsyncMock, return_value=self.records):
            records_ids = self.loop.run_until_complete(context.get_records_ids())

        assert records_ids == [1, 2]

    def test_get_records_ids_should_return_empty_list_if_no_corresponding_id(self):
        context = ActionContextBulk(
            self.decorated_collection, self.mocked_caller, {"title": "Foundation"}, PaginatedFilter({})
        )

        with patch.object(self.collection_book, "list", new_callable=AsyncMock, return_value=[]):
            records_ids = self.loop.run_until_complete(context.get_records_ids())

        assert records_ids == []
