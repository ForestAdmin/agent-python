import asyncio
import importlib
import json
import sys
from datetime import date, datetime
from unittest import TestCase
from unittest.mock import AsyncMock, Mock, patch

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

import forestadmin.agent_toolkit.resources.collections.stats
from forestadmin.agent_toolkit.options import Options
from forestadmin.agent_toolkit.resources.collections.filter import build_filter
from forestadmin.agent_toolkit.resources.collections.requests import RequestCollection
from forestadmin.agent_toolkit.services.permissions.ip_whitelist_service import IpWhiteListService
from forestadmin.agent_toolkit.services.permissions.permission_service import PermissionService
from forestadmin.agent_toolkit.utils.context import Request, RequestMethod, User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.exceptions import ForestException
from forestadmin.datasource_toolkit.interfaces.fields import FieldType, Operator, PrimitiveType


def authenticate_mock(fn):
    async def wrapped2(self, request):
        request.user = User(
            rendering_id=1,
            user_id=1,
            tags={},
            email="dummy@user.fr",
            first_name="dummy",
            last_name="user",
            team="operational",
            timezone=zoneinfo.ZoneInfo("Europe/Paris"),
        )

        return await fn(self, request)

    return wrapped2


def ip_white_list_mock(decorated_fn):
    async def wrapped(self, request: Request, *args, **kwargs):
        return await decorated_fn(self, request, *args, **kwargs)

    return wrapped


patch("forestadmin.agent_toolkit.resources.collections.decorators.authenticate", authenticate_mock).start()
patch("forestadmin.agent_toolkit.resources.collections.decorators.ip_white_list", ip_white_list_mock).start()


# how to mock decorators, and why they are not testable :
# https://dev.to/stack-labs/how-to-mock-a-decorator-in-python-55jc

importlib.reload(forestadmin.agent_toolkit.resources.collections.stats)
from forestadmin.agent_toolkit.resources.collections.stats import StatsResource  # noqa: E402


class TestStatResource(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()
        cls.ip_white_list_service = Mock(IpWhiteListService)
        cls.ip_white_list_service.is_enable = AsyncMock(return_value=False)

        cls.permission_service = Mock(PermissionService)
        cls.permission_service.get_scope = AsyncMock(return_value=None)
        cls.permission_service.can_chart = AsyncMock(return_value=True)
        cls.permission_service.get_user_data = AsyncMock(
            return_value={
                "id": 1,
                "firstName": "dummy",
                "lastName": "user",
                "fullName": "dummy user",
                "email": "dummy@user.fr",
                "tags": {},
                "roleId": 1,
                "permissionLevel": "admin",
            }
        )
        cls.permission_service.get_team = AsyncMock(return_value={"id": 7, "name": "Operations"})
        cls.options = Options(
            auth_secret="fake_secret",
            env_secret="fake_secret",
            server_url="http://fake:5000",
            prefix="",
            is_production=False,
        )
        cls.datasource = Datasource()
        Collection.__abstractmethods__ = set()  # to instantiate abstract class
        cls.book_collection = Collection("Book", cls.datasource)
        cls.book_collection.add_fields(
            {
                "id": {"column_type": PrimitiveType.NUMBER, "is_primary_key": True, "type": FieldType.COLUMN},
                "title": {"column_type": PrimitiveType.STRING, "is_primary_key": False, "type": FieldType.COLUMN},
                "price": {"column_type": PrimitiveType.NUMBER, "is_primary_key": False, "type": FieldType.COLUMN},
                "date": {
                    "column_type": PrimitiveType.DATE_ONLY,
                    "is_primary_key": False,
                    "type": FieldType.COLUMN,
                    "filter_operators": set([Operator.YESTERDAY]),
                    "validations": [],
                },
                "year": {
                    "column_type": PrimitiveType.NUMBER,
                    "is_primary_key": False,
                    "type": FieldType.COLUMN,
                    "filter_operators": set([Operator.EQUAL]),
                },
                "reviews": {
                    "type": FieldType.MANY_TO_MANY,
                    "origin_key": "book_id",
                    "origin_key_target": "id",
                    "foreign_key": "review_id",
                    "foreign_key_target": "id",
                    "foreign_collection": "Review",
                    "through_collection": "BookReview",
                },
                "book_reviews": {
                    "type": FieldType.ONE_TO_MANY,
                    "origin_key": "book_id",
                    "origin_key_target": "id",
                    "foreign_collection": "Review",
                },
            }
        )
        cls.datasource.add_collection(cls.book_collection)

        cls.book_review_collection = Collection("BookReview", cls.datasource)
        cls.book_review_collection.add_fields(
            {
                "id": {"column_type": PrimitiveType.NUMBER, "is_primary_key": True, "type": FieldType.COLUMN},
                "book_id": {"column_type": PrimitiveType.NUMBER, "is_primary_key": False, "type": FieldType.COLUMN},
                "review_id": {"column_type": PrimitiveType.NUMBER, "is_primary_key": False, "type": FieldType.COLUMN},
                "book": {
                    "type": FieldType.MANY_TO_ONE,
                    "foreign_key": "book_id",
                    "foreign_key_target": "id",
                    "foreign_collection": "Book",
                },
                "reviews": {
                    "type": FieldType.MANY_TO_ONE,
                    "foreign_key": "review_id",
                    "foreign_key_target": "id",
                    "foreign_collection": "Review",
                },
            }
        )
        cls.datasource.add_collection(cls.book_review_collection)

        cls.review_collection = Collection("Review", cls.datasource)
        cls.review_collection.add_fields(
            {
                "id": {"column_type": PrimitiveType.NUMBER, "is_primary_key": True, "type": FieldType.COLUMN},
                "author": {"column_type": PrimitiveType.STRING, "is_primary_key": False, "type": FieldType.COLUMN},
                "books": {
                    "type": FieldType.MANY_TO_ONE,
                    "foreign_key": "book_id",
                    "foreign_key_target": "id",
                    "foreign_collection": "Books",
                },
            }
        )
        cls.datasource.add_collection(cls.review_collection)

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
        self.stat_resource = StatsResource(
            self.datasource, self.permission_service, self.ip_white_list_service, self.options
        )


class TestDispatchStatsResource(TestStatResource):
    def test_dispatch_should_return_error_if_no_collection_specified(self):
        request = Request(
            method=RequestMethod.POST,
            headers={},
            query={},
            user=self.mocked_caller,
        )
        response = self.loop.run_until_complete(self.stat_resource.dispatch(request, None))
        content_body = json.loads(response.body)
        self.assertEqual(response.status, 500)
        self.assertEqual(content_body["errors"][0]["name"], "RequestCollectionException")
        self.assertEqual(content_body["errors"][0]["detail"], "🌳🌳🌳'collection_name' is missing in the request")

    def test_dispatch_should_return_error_if_bad_collection_specified(self):
        request = Request(
            method=RequestMethod.POST,
            headers={},
            query={"collection_name": "fakeCollection"},
            user=self.mocked_caller,
        )
        response = self.loop.run_until_complete(self.stat_resource.dispatch(request, None))
        content_body = json.loads(response.body)
        self.assertEqual(response.status, 500)
        self.assertEqual(content_body["errors"][0]["name"], "RequestCollectionException")
        self.assertEqual(content_body["errors"][0]["detail"], "🌳🌳🌳Collection 'fakeCollection' not found")

    def test_dispatch_should_return_error_if_chart_type_not_specified(self):
        request = Request(
            method=RequestMethod.POST,
            headers={},
            query={"collection_name": "Book"},
            user=self.mocked_caller,
        )
        response = self.loop.run_until_complete(self.stat_resource.dispatch(request, None))
        content_body = json.loads(response.body)
        self.assertEqual(response.status, 500)
        self.assertEqual(content_body["errors"][0]["name"], "ForestException")
        self.assertEqual(content_body["errors"][0]["detail"], "🌳🌳🌳Missing stats type in request body")

    def test_dispatch_should_return_error_if_bad_chart_type_specified(self):
        request = Request(
            method=RequestMethod.POST,
            headers={},
            query={"collection_name": "Book"},
            body={"type": "Unknown"},
            user=self.mocked_caller,
        )
        response = self.loop.run_until_complete(self.stat_resource.dispatch(request, None))
        content_body = json.loads(response.body)
        self.assertEqual(response.status, 500)
        self.assertEqual(content_body["errors"][0]["name"], "ForestException")
        self.assertEqual(content_body["errors"][0]["detail"], "🌳🌳🌳Unknown stats type Unknown")

    def test_dispatch_should_call_value_for_value_charts(self):
        request = Request(
            method=RequestMethod.POST,
            headers={},
            query={"collection_name": "Book"},
            body={"type": "Value"},
            user=self.mocked_caller,
        )
        with patch.object(self.stat_resource, "value", new_callable=AsyncMock, return_value="value") as mock_value:
            response = self.loop.run_until_complete(self.stat_resource.dispatch(request, None))
            mock_value.assert_awaited_once()
            self.assertEqual(mock_value.await_args.args[0].method, RequestMethod.POST)
            self.assertEqual(mock_value.await_args.args[0].collection, self.book_collection)
            self.assertEqual(mock_value.await_args.args[0].query, {"collection_name": "Book"})
            self.assertEqual(mock_value.await_args.args[0].body, {"type": "Value"})
            self.assertEqual(mock_value.await_args.args[0].user, self.mocked_caller)
        self.assertEqual(response, "value")

    def test_dispatch_should_call_value_for_objective_charts(self):
        request = Request(
            method=RequestMethod.POST,
            headers={},
            query={"collection_name": "Book"},
            body={"type": "Objective"},
            user=self.mocked_caller,
        )
        with patch.object(
            self.stat_resource, "objective", new_callable=AsyncMock, return_value="objective"
        ) as mock_objective:
            response = self.loop.run_until_complete(self.stat_resource.dispatch(request, None))
            mock_objective.assert_awaited_once()
            self.assertEqual(mock_objective.await_args.args[0].method, RequestMethod.POST)
            self.assertEqual(mock_objective.await_args.args[0].collection, self.book_collection)
            self.assertEqual(mock_objective.await_args.args[0].query, {"collection_name": "Book"})
            self.assertEqual(mock_objective.await_args.args[0].body, {"type": "Objective"})
            self.assertEqual(mock_objective.await_args.args[0].user, self.mocked_caller)
        self.assertEqual(response, "objective")

    def test_dispatch_should_call_value_for_pie_charts(self):
        request = Request(
            method=RequestMethod.POST,
            headers={},
            query={"collection_name": "Book"},
            body={"type": "Pie"},
            user=self.mocked_caller,
        )
        with patch.object(self.stat_resource, "pie", new_callable=AsyncMock, return_value="pie") as mock_pie:
            response = self.loop.run_until_complete(self.stat_resource.dispatch(request, None))
            mock_pie.assert_awaited_once()
            self.assertEqual(mock_pie.await_args.args[0].method, RequestMethod.POST)
            self.assertEqual(mock_pie.await_args.args[0].collection, self.book_collection)
            self.assertEqual(mock_pie.await_args.args[0].query, {"collection_name": "Book"})
            self.assertEqual(mock_pie.await_args.args[0].body, {"type": "Pie"})
            self.assertEqual(mock_pie.await_args.args[0].user, self.mocked_caller)
        self.assertEqual(response, "pie")

    def test_dispatch_should_call_value_for_line_charts(self):
        request = Request(
            method=RequestMethod.POST,
            headers={},
            query={"collection_name": "Book"},
            body={"type": "Line"},
            user=self.mocked_caller,
        )
        with patch.object(self.stat_resource, "line", new_callable=AsyncMock, return_value="line") as mock_line:
            response = self.loop.run_until_complete(self.stat_resource.dispatch(request, None))
            mock_line.assert_awaited_once()
            self.assertEqual(mock_line.await_args.args[0].method, RequestMethod.POST)
            self.assertEqual(mock_line.await_args.args[0].collection, self.book_collection)
            self.assertEqual(mock_line.await_args.args[0].query, {"collection_name": "Book"})
            self.assertEqual(mock_line.await_args.args[0].body, {"type": "Line"})
            self.assertEqual(mock_line.await_args.args[0].user, self.mocked_caller)
        self.assertEqual(response, "line")

    def test_dispatch_should_call_value_for_leaderboard_charts(self):
        request = Request(
            method=RequestMethod.POST,
            headers={},
            query={"collection_name": "Book"},
            body={"type": "Leaderboard"},
            user=self.mocked_caller,
        )
        with patch.object(
            self.stat_resource, "leader_board", new_callable=AsyncMock, return_value="leader_board"
        ) as mock_leader_board:
            response = self.loop.run_until_complete(self.stat_resource.dispatch(request, None))
            mock_leader_board.assert_awaited_once()
            self.assertEqual(mock_leader_board.await_args.args[0].method, RequestMethod.POST)
            self.assertEqual(mock_leader_board.await_args.args[0].collection, self.book_collection)
            self.assertEqual(mock_leader_board.await_args.args[0].query, {"collection_name": "Book"})
            self.assertEqual(mock_leader_board.await_args.args[0].body, {"type": "Leaderboard"})
            self.assertEqual(mock_leader_board.await_args.args[0].user, self.mocked_caller)
        self.assertEqual(response, "leader_board")

    def test_dispatch_should_return_error_when_chart_method_raise(self):
        request = Request(
            method=RequestMethod.POST,
            headers={},
            query={"collection_name": "Book"},
            body={"type": "Leaderboard"},
            user=self.mocked_caller,
        )
        with patch.object(
            self.stat_resource, "leader_board", new_callable=AsyncMock, side_effect=Exception("raise")
        ) as mock_leader_board:
            response = self.loop.run_until_complete(self.stat_resource.dispatch(request, None))
            mock_leader_board.assert_awaited_once()

        content_body = json.loads(response.body)
        self.assertEqual(response.status, 500)
        self.assertEqual(content_body["errors"][0]["name"], "Exception")
        self.assertEqual(content_body["errors"][0]["detail"], "raise")


class TestValueStatsResource(TestStatResource):
    def mk_request(self, filter_):
        return RequestCollection(
            method=RequestMethod.POST,
            collection=self.book_collection,
            body={
                "aggregateFieldName": "price",
                "aggregator": "Sum",
                "sourceCollectionName": "Book",
                "type": "Value",
                "timezone": "Europe/Paris",
                "filter": filter_,
                "contextVariables": {"dropdown1.selectedValue": 2022},
            },
            query={
                "collection_name": "Book",
                "timezone": "Europe/Paris",
            },
            headers={},
            user=self.mocked_caller,
        )

    def test_value_should_raise_if_no_request_body(self):
        request = RequestCollection(
            method=RequestMethod.POST,
            collection=self.book_collection,
            query={
                "collection_name": "Book",
                "timezone": "Europe/Paris",
            },
            headers={},
            user=self.mocked_caller,
        )
        self.assertRaisesRegex(Exception, "", self.loop.run_until_complete, self.stat_resource.value(request))

    def test_value_should_return_correct_value_with_variable_injection(self):
        request = self.mk_request(
            {
                "aggregator": "and",
                "conditions": [{"operator": "equal", "value": "{{dropdown1.selectedValue}}", "field": "year"}],
            }
        )
        with patch.object(
            self.book_collection, "aggregate", new_callable=AsyncMock, return_value=[{"value": 10, "group": {}}]
        ) as mock_aggregate:
            with patch(
                "forestadmin.agent_toolkit.resources.collections.stats.build_filter",
                wraps=build_filter,
            ) as mock_build_filter:
                response = self.loop.run_until_complete(self.stat_resource.value(request))
                mock_build_filter.assert_called_once()
                self.assertEqual(mock_build_filter.call_args_list[0][0][0].body["filter"]["field"], "year")
                self.assertEqual(mock_build_filter.call_args_list[0][0][0].body["filter"]["operator"], "equal")
                self.assertEqual(mock_build_filter.call_args_list[0][0][0].body["filter"]["value"], 2022)
            mock_aggregate.assert_awaited_once()
        content_body = json.loads(response.body)
        self.assertEqual(response.status, 200)
        self.assertEqual(content_body["data"]["type"], "stats")
        self.assertEqual(content_body["data"]["attributes"]["value"]["countCurrent"], 10)

    def test_value_should_work_with_previous_value(self):
        request = self.mk_request(
            {
                "aggregator": "and",
                "conditions": [{"operator": "yesterday", "value": None, "field": "date"}],
            }
        )
        call_cnt = {"aggregate": 0}

        def aggregate_mock(*args, **kwargs):
            call_cnt["aggregate"] = call_cnt["aggregate"] + 1
            if call_cnt["aggregate"] == 1:
                return [{"value": 10, "group": {}}]
            elif call_cnt["aggregate"] == 2:
                return [{"value": 20, "group": {}}]

        with patch.object(self.book_collection, "aggregate", new_callable=AsyncMock, side_effect=aggregate_mock):
            response = self.loop.run_until_complete(self.stat_resource.value(request))
        content_body = json.loads(response.body)
        self.assertEqual(response.status, 200)
        self.assertEqual(content_body["data"]["type"], "stats")
        self.assertEqual(content_body["data"]["attributes"]["value"]["countCurrent"], 10)
        self.assertEqual(content_body["data"]["attributes"]["value"]["countPrevious"], 20)


class TestObjectiveStatsResource(TestStatResource):
    def mk_request(self):
        return RequestCollection(
            method=RequestMethod.POST,
            collection=self.book_collection,
            body={
                "type": "Objective",
                "sourceCollectionName": "Book",
                "aggregateFieldName": "price",
                "aggregator": "Count",
                "filter": None,
                "timezone": "Europe/Paris",
            },
            query={
                "collection_name": "Book",
                "timezone": "Europe/Paris",
            },
            headers={},
            user=self.mocked_caller,
        )

    def test_value_should_raise_if_no_request_body(self):
        request = RequestCollection(
            method=RequestMethod.POST,
            collection=self.book_collection,
            query={
                "collection_name": "Book",
                "timezone": "Europe/Paris",
            },
            headers={},
            user=self.mocked_caller,
        )
        self.assertRaisesRegex(Exception, "", self.loop.run_until_complete, self.stat_resource.objective(request))

    def test_pie_should_return_correct_pie_chart(self):
        request = self.mk_request()

        with patch.object(
            self.book_collection,
            "aggregate",
            new_callable=AsyncMock,
            return_value=[{"value": 10, "group": {}}],
        ):
            response = self.loop.run_until_complete(self.stat_resource.objective(request))
        content_body = json.loads(response.body)
        self.assertEqual(response.status, 200)
        self.assertEqual(content_body["data"]["type"], "stats")
        self.assertEqual(content_body["data"]["attributes"]["value"], {"value": 10})


class TestPieStatsResource(TestStatResource):
    def mk_request(self):
        return RequestCollection(
            method=RequestMethod.POST,
            collection=self.book_collection,
            body={
                "type": "Pie",
                "sourceCollectionName": "Book",
                "groupByFieldName": "year",
                "aggregator": "Count",
                "timezone": "Europe/Paris",
            },
            query={
                "collection_name": "Book",
                "timezone": "Europe/Paris",
            },
            headers={},
            user=self.mocked_caller,
        )

    def test_value_should_raise_if_no_request_body(self):
        request = RequestCollection(
            method=RequestMethod.POST,
            collection=self.book_collection,
            query={
                "collection_name": "Book",
                "timezone": "Europe/Paris",
            },
            headers={},
            user=self.mocked_caller,
        )
        self.assertRaisesRegex(Exception, "", self.loop.run_until_complete, self.stat_resource.pie(request))

    def test_pie_should_return_correct_pie_chart(self):
        request = self.mk_request()

        with patch.object(
            self.book_collection,
            "aggregate",
            new_callable=AsyncMock,
            return_value=[{"value": 100, "group": {"year": 2021}}, {"value": 150, "group": {"year": 2022}}],
        ):
            response = self.loop.run_until_complete(self.stat_resource.pie(request))
        content_body = json.loads(response.body)
        self.assertEqual(response.status, 200)
        self.assertEqual(content_body["data"]["type"], "stats")
        self.assertEqual(
            content_body["data"]["attributes"]["value"], [{"key": 2021, "value": 100}, {"key": 2022, "value": 150}]
        )


class TestLineStatsResource(TestStatResource):
    def mk_request(self, timerange):
        return RequestCollection(
            method=RequestMethod.POST,
            collection=self.book_collection,
            body={
                "type": "Line",
                "sourceCollectionName": "Book",
                "groupByFieldName": "date",
                "aggregator": "Count",
                "timeRange": timerange,
                "timezone": "Europe/Paris",
            },
            query={
                "collection_name": "Book",
                "timezone": "Europe/Paris",
            },
            headers={},
            user=self.mocked_caller,
        )

    def test_value_should_raise_if_no_request_body(self):
        request = RequestCollection(
            method=RequestMethod.POST,
            collection=self.book_collection,
            query={
                "collection_name": "Book",
                "timezone": "Europe/Paris",
            },
            headers={},
            user=self.mocked_caller,
        )
        self.assertRaisesRegex(Exception, "", self.loop.run_until_complete, self.stat_resource.line(request))

    def test_line_should_return_chart_with_day_filter(self):
        request = self.mk_request("Day")
        with patch.object(
            self.book_collection,
            "aggregate",
            new_callable=AsyncMock,
            return_value=[
                {"value": 10, "group": {"date": "2022-01-03 00:00:00"}},
                {"value": 15, "group": {"date": "2022-01-10 00:00:00"}},
            ],
        ):
            response = self.loop.run_until_complete(self.stat_resource.line(request))

        content_body = json.loads(response.body)
        self.assertEqual(response.status, 200)
        self.assertEqual(content_body["data"]["type"], "stats")
        self.assertEqual(len(content_body["data"]["attributes"]["value"]), 8)
        self.assertEqual(
            content_body["data"]["attributes"]["value"][0], {"label": "03/01/2022", "values": {"value": 10}}
        )
        self.assertEqual(
            content_body["data"]["attributes"]["value"][-1],
            {"label": "10/01/2022", "values": {"value": 15}},
        )

    def test_line_should_return_chart_with_week_filter(self):
        request = self.mk_request("Week")
        with patch.object(
            self.book_collection,
            "aggregate",
            new_callable=AsyncMock,
            return_value=[
                {"value": 10, "group": {"date": "2022-01-03 00:00:00"}},
                {"value": 15, "group": {"date": "2022-01-10 00:00:00"}},
            ],
        ):
            response = self.loop.run_until_complete(self.stat_resource.line(request))

        content_body = json.loads(response.body)
        self.assertEqual(response.status, 200)
        self.assertEqual(content_body["data"]["type"], "stats")
        self.assertEqual(len(content_body["data"]["attributes"]["value"]), 2)
        self.assertEqual(content_body["data"]["attributes"]["value"][0], {"label": "W01-2022", "values": {"value": 10}})
        self.assertEqual(
            content_body["data"]["attributes"]["value"][-1],
            {"label": "W02-2022", "values": {"value": 15}},
        )

    def test_line_should_return_chart_with_month_filter(self):
        request = self.mk_request("Month")
        with patch.object(
            self.book_collection,
            "aggregate",
            new_callable=AsyncMock,
            return_value=[
                {"value": 10, "group": {"date": "2022-01-03 00:00:00"}},
                {"value": 15, "group": {"date": "2022-02-03 00:00:00"}},
            ],
        ):
            response = self.loop.run_until_complete(self.stat_resource.line(request))

        content_body = json.loads(response.body)
        self.assertEqual(response.status, 200)
        self.assertEqual(content_body["data"]["type"], "stats")
        self.assertEqual(len(content_body["data"]["attributes"]["value"]), 2)
        self.assertEqual(content_body["data"]["attributes"]["value"][0], {"label": "Jan 2022", "values": {"value": 10}})
        self.assertEqual(
            content_body["data"]["attributes"]["value"][-1],
            {"label": "Feb 2022", "values": {"value": 15}},
        )

    def test_line_should_return_chart_with_year_filter(self):
        request = self.mk_request("Year")
        with patch.object(
            self.book_collection,
            "aggregate",
            new_callable=AsyncMock,
            return_value=[
                {"value": 10, "group": {"date": "2022-01-03 00:00:00"}},
                {"value": 15, "group": {"date": "2023-02-03 00:00:00"}},
            ],
        ):
            response = self.loop.run_until_complete(self.stat_resource.line(request))

        content_body = json.loads(response.body)
        self.assertEqual(response.status, 200)
        self.assertEqual(content_body["data"]["type"], "stats")
        self.assertEqual(len(content_body["data"]["attributes"]["value"]), 2)
        self.assertEqual(content_body["data"]["attributes"]["value"][0], {"label": "2022", "values": {"value": 10}})
        self.assertEqual(
            content_body["data"]["attributes"]["value"][-1],
            {"label": "2023", "values": {"value": 15}},
        )

    def test_line_should_raise_if_timeRange_not_defined(self):
        request = RequestCollection(
            method=RequestMethod.POST,
            collection=self.book_collection,
            body={
                "type": "Line",
                "sourceCollectionName": "Book",
                "groupByFieldName": "date",
                "aggregator": "Count",
                "timezone": "Europe/Paris",
            },
            query={
                "collection_name": "Book",
                "timezone": "Europe/Paris",
            },
            headers={},
            user=self.mocked_caller,
        )
        self.assertRaisesRegex(
            ForestException,
            r"🌳🌳🌳The parameter timeRange is not defined",
            self.loop.run_until_complete,
            self.stat_resource.line(request),
        )

    def test_line_should_work_if_collection_return_date_as_str(self):
        request = self.mk_request("Week")
        with patch.object(
            self.book_collection,
            "aggregate",
            new_callable=AsyncMock,
            return_value=[
                {"value": 10, "group": {"date": "2022-01-03 00:00:00"}},
                {"value": 15, "group": {"date": "2022-01-10 00:00:00"}},
            ],
        ):
            response = self.loop.run_until_complete(self.stat_resource.line(request))

        content_body = json.loads(response.body)
        self.assertEqual(response.status, 200)
        self.assertEqual(content_body["data"]["type"], "stats")
        self.assertEqual(len(content_body["data"]["attributes"]["value"]), 2)
        self.assertEqual(content_body["data"]["attributes"]["value"][0], {"label": "W01-2022", "values": {"value": 10}})
        self.assertEqual(
            content_body["data"]["attributes"]["value"][-1],
            {"label": "W02-2022", "values": {"value": 15}},
        )

    def test_line_should_work_if_collection_return_date_as_date(self):
        request = self.mk_request("Week")
        with patch.object(
            self.book_collection,
            "aggregate",
            new_callable=AsyncMock,
            return_value=[
                {"value": 10, "group": {"date": date(2022, 1, 3)}},
                {"value": 15, "group": {"date": date(2022, 1, 10)}},
            ],
        ):
            response = self.loop.run_until_complete(self.stat_resource.line(request))

        content_body = json.loads(response.body)
        self.assertEqual(response.status, 200)
        self.assertEqual(content_body["data"]["type"], "stats")
        self.assertEqual(len(content_body["data"]["attributes"]["value"]), 2)
        self.assertEqual(content_body["data"]["attributes"]["value"][0], {"label": "W01-2022", "values": {"value": 10}})
        self.assertEqual(
            content_body["data"]["attributes"]["value"][-1],
            {"label": "W02-2022", "values": {"value": 15}},
        )

    def test_line_should_work_if_collection_return_date_as_datetime(self):
        request = self.mk_request("Week")
        with patch.object(
            self.book_collection,
            "aggregate",
            new_callable=AsyncMock,
            return_value=[
                {"value": 10, "group": {"date": datetime(2022, 1, 3, 0, 0, 0)}},
                {"value": 15, "group": {"date": datetime(2022, 1, 10, 0, 0, 0)}},
            ],
        ):
            response = self.loop.run_until_complete(self.stat_resource.line(request))

        content_body = json.loads(response.body)
        self.assertEqual(response.status, 200)
        self.assertEqual(content_body["data"]["type"], "stats")
        self.assertEqual(len(content_body["data"]["attributes"]["value"]), 2)
        self.assertEqual(content_body["data"]["attributes"]["value"][0], {"label": "W01-2022", "values": {"value": 10}})
        self.assertEqual(
            content_body["data"]["attributes"]["value"][-1],
            {"label": "W02-2022", "values": {"value": 15}},
        )


class TestLeaderBoradStatsResource(TestStatResource):
    def mk_request(self, relation_field_name):
        return RequestCollection(
            method=RequestMethod.POST,
            collection=self.book_collection,
            body={
                "type": "Leaderboard",
                "sourceCollectionName": "Book",
                "labelFieldName": "title",
                "aggregator": "Count",
                "relationshipFieldName": relation_field_name,
                "timezone": "Europe/Paris",
            },
            query={
                "collection_name": "Book",
                "timezone": "Europe/Paris",
            },
            headers={},
            user=self.mocked_caller,
        )

    def test_leaderbaord_should_raise_if_no_request_body(self):
        request = RequestCollection(
            method=RequestMethod.POST,
            collection=self.book_collection,
            query={
                "collection_name": "Book",
                "timezone": "Europe/Paris",
            },
            headers={},
            user=self.mocked_caller,
        )
        self.assertRaisesRegex(Exception, "", self.loop.run_until_complete, self.stat_resource.leader_board(request))

    def test_leaderbaord_should_work_on_one_to_many_field(self):
        request = self.mk_request("book_reviews")
        with patch.object(
            self.book_collection,
            "aggregate",
            new_callable=AsyncMock,
            return_value=[
                {"value": 15, "group": {"title": "Foundation"}},
                {"value": 20, "group": {"title": "Harry Potter"}},
            ],
        ):
            response = self.loop.run_until_complete(self.stat_resource.leader_board(request))

        content_body = json.loads(response.body)
        self.assertEqual(response.status, 200)
        self.assertEqual(content_body["data"]["type"], "stats")
        self.assertEqual(len(content_body["data"]["attributes"]["value"]), 2)
        self.assertEqual(content_body["data"]["attributes"]["value"][0], {"key": "Foundation", "value": 15})
        self.assertEqual(content_body["data"]["attributes"]["value"][1], {"key": "Harry Potter", "value": 20})

    def test_leaderbaord_should_work_on_many_to_many_field(self):
        request = self.mk_request("reviews")
        with patch.object(
            self.book_collection,
            "aggregate",
            new_callable=AsyncMock,
            return_value=[
                {"value": 15, "group": {"title": "Foundation"}},
                {"value": 20, "group": {"title": "Harry Potter"}},
            ],
        ):
            response = self.loop.run_until_complete(self.stat_resource.leader_board(request))

        content_body = json.loads(response.body)
        self.assertEqual(response.status, 200)
        self.assertEqual(content_body["data"]["type"], "stats")
        self.assertEqual(len(content_body["data"]["attributes"]["value"]), 2)
        self.assertEqual(content_body["data"]["attributes"]["value"][0], {"key": "Foundation", "value": 15})
        self.assertEqual(content_body["data"]["attributes"]["value"][1], {"key": "Harry Potter", "value": 20})

    def test_leaderbaord_should_raise_when_request_not_filled_correctly(self):
        request = RequestCollection(
            method=RequestMethod.POST,
            collection=self.book_collection,
            body={
                "type": "Leaderboard",
                "aggregator": "Count",
                "sourceCollectionName": "Book",
                "relationshipFieldName": "reviews",
                "timezone": "Europe/Paris",
            },
            query={
                "collection_name": "Book",
                "timezone": "Europe/Paris",
            },
            headers={},
            user=self.mocked_caller,
        )

        self.assertRaisesRegex(
            ForestException,
            r"🌳🌳🌳The parameter labelFieldName is not defined",
            self.loop.run_until_complete,
            self.stat_resource.leader_board(request),
        )
