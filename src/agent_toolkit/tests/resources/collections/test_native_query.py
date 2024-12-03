import asyncio
import importlib
import json
import sys
from unittest import TestCase
from unittest.mock import AsyncMock, Mock, patch

import forestadmin.agent_toolkit.resources.collections.native_query

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

import forestadmin.agent_toolkit.resources.collections.crud
from forestadmin.agent_toolkit.options import Options
from forestadmin.agent_toolkit.services.permissions.ip_whitelist_service import IpWhiteListService
from forestadmin.agent_toolkit.services.permissions.permission_service import PermissionService
from forestadmin.agent_toolkit.utils.context import Request, RequestMethod, User
from forestadmin.datasource_toolkit.datasource_customizer.datasource_composite import CompositeDatasource
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.exceptions import ForbiddenError


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
            request={"ip": "127.0.0.1"},
        )

        return await fn(self, request)

    return wrapped2


def ip_white_list_mock(fn):
    async def wrapped(self, request: Request, *args, **kwargs):
        return await fn(self, request, *args, **kwargs)

    return wrapped


patch("forestadmin.agent_toolkit.resources.collections.decorators.authenticate", authenticate_mock).start()
patch("forestadmin.agent_toolkit.resources.collections.decorators.ip_white_list", ip_white_list_mock).start()
# how to mock decorators, and why they are not testable :
# https://dev.to/stack-labs/how-to-mock-a-decorator-in-python-55jc

importlib.reload(forestadmin.agent_toolkit.resources.collections.native_query)
from forestadmin.agent_toolkit.resources.collections.native_query import NativeQueryResource  # noqa: E402


class TestNativeQueryResourceBase(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()
        cls.options = Options(
            auth_secret="fake_secret",
            env_secret="fake_secret",
            server_url="http://fake:5000",
            prefix="",
            is_production=False,
        )
        # cls.datasource = Mock(Datasource)
        cls.datasource = Datasource(["db1", "db2"])
        cls.datasource_composite = CompositeDatasource()
        cls.datasource_composite.add_datasource(cls.datasource)

    def setUp(self):
        self.datasource_composite.execute_native_query = AsyncMock()
        self.ip_white_list_service = Mock(IpWhiteListService)
        self.ip_white_list_service.is_enable = AsyncMock(return_value=False)

        self.permission_service = Mock(PermissionService)
        self.permission_service.can_chart = AsyncMock(return_value=None)

        self.native_query_resource = NativeQueryResource(
            self.datasource_composite,
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            self.options,
        )


class TestNativeQueryResourceOnError(TestNativeQueryResourceBase):
    def test_should_return_error_if_cannot_chart_on_permission(self):
        request = Request(
            method=RequestMethod.POST,
            headers={},
            body={},
            client_ip="127.0.0.1",
            query={},
        )
        with patch.object(
            self.permission_service,
            "can_chart",
            new_callable=AsyncMock,
            side_effect=ForbiddenError("You don't have permission to access this chart."),
        ) as mock_can_chart:
            response = self.loop.run_until_complete(
                self.native_query_resource.dispatch(request, "native_query"),
            )
            self.assertEqual(response.status, 403)
            self.assertEqual(response.headers, {"content-type": "application/json"})
            response_body = json.loads(response.body)
            self.assertEqual(
                response_body,
                {
                    "errors": [
                        {
                            "name": "ForbiddenError",
                            "detail": "You don't have permission to access this chart.",
                            "status": 403,
                            "data": {},
                        }
                    ]
                },
            )

            mock_can_chart.assert_awaited_once_with(request)

    def test_should_return_error_if_connectionName_is_not_here(self):
        request = Request(
            method=RequestMethod.POST,
            headers={},
            body={},
            client_ip="127.0.0.1",
            query={},
        )
        response = self.loop.run_until_complete(
            self.native_query_resource.dispatch(request, "native_query"),
        )
        self.assertEqual(response.status, 400)
        self.assertEqual(response.headers, {"content-type": "application/json"})
        response_body = json.loads(response.body)
        self.assertEqual(
            response_body,
            {
                "errors": [
                    {
                        "name": "ValidationError",
                        "detail": "Setting a 'Native query connection' is mandatory.",
                        "status": 400,
                        "data": {},
                    }
                ]
            },
        )

    def test_should_return_error_if_query_is_not_here(self):
        request = Request(
            method=RequestMethod.POST,
            headers={},
            body={"connectionName": "db1"},
            client_ip="127.0.0.1",
            query={},
        )
        response = self.loop.run_until_complete(
            self.native_query_resource.dispatch(request, "native_query"),
        )
        self.assertEqual(response.status, 400)
        self.assertEqual(response.headers, {"content-type": "application/json"})
        response_body = json.loads(response.body)
        self.assertEqual(
            response_body,
            {
                "errors": [
                    {
                        "name": "ValidationError",
                        "detail": "Missing 'query' in parameter.",
                        "status": 400,
                        "data": {},
                    }
                ]
            },
        )

    def test_should_return_error_if_chart_type_is_unknown_or_missing(self):
        request = Request(
            method=RequestMethod.POST,
            headers={},
            body={"connectionName": "db1", "query": "select count(*) from orders;"},
            client_ip="127.0.0.1",
            query={},
        )
        response = self.loop.run_until_complete(
            self.native_query_resource.dispatch(request, "native_query"),
        )
        self.assertEqual(response.status, 400)
        self.assertEqual(response.headers, {"content-type": "application/json"})
        response_body = json.loads(response.body)
        self.assertEqual(
            response_body,
            {
                "errors": [
                    {
                        "name": "ValidationError",
                        "detail": "Unknown chart type 'None'.",
                        "status": 400,
                        "data": {},
                    }
                ]
            },
        )

        request.body["type"] = "unknown"
        response = self.loop.run_until_complete(
            self.native_query_resource.dispatch(request, "native_query"),
        )
        self.assertEqual(response.status, 400)
        self.assertEqual(response.headers, {"content-type": "application/json"})
        response_body = json.loads(response.body)
        self.assertEqual(
            response_body,
            {
                "errors": [
                    {
                        "name": "ValidationError",
                        "detail": "Unknown chart type 'unknown'.",
                        "status": 400,
                        "data": {},
                    }
                ]
            },
        )


class TestNativeQueryResourceValueChart(TestNativeQueryResourceBase):
    def test_should_correctly_handle_value_chart(self):
        native_query = "select count(*) as value from orders;"
        request = Request(
            method=RequestMethod.POST,
            headers={},
            body={"connectionName": "db1", "query": native_query, "type": "Value"},
            client_ip="127.0.0.1",
            query={},
        )
        with patch.object(
            self.datasource_composite, "execute_native_query", new_callable=AsyncMock, return_value=[{"value": 100}]
        ) as mock_exec_native_query:
            response = self.loop.run_until_complete(
                self.native_query_resource.dispatch(request, "native_query"),
            )
            mock_exec_native_query.assert_awaited_once_with("db1", native_query, {})

        self.assertEqual(response.status, 200)
        self.assertEqual(response.headers, {"content-type": "application/json"})
        response_body = json.loads(response.body)
        self.assertIn("id", response_body["data"])
        self.assertEqual(response_body["data"]["type"], "stats")
        self.assertEqual(response_body["data"]["attributes"], {"value": {"countCurrent": 100}})

    def test_should_return_error_if_value_query_return_fields_are_not_good(self):
        native_query = "select count(*) as not_value from orders;"
        request = Request(
            method=RequestMethod.POST,
            headers={},
            body={"connectionName": "db1", "query": native_query, "type": "Value"},
            client_ip="127.0.0.1",
            query={},
        )
        with patch.object(
            self.datasource_composite, "execute_native_query", new_callable=AsyncMock, return_value=[{"not_value": 100}]
        ) as mock_exec_native_query:
            response = self.loop.run_until_complete(
                self.native_query_resource.dispatch(request, "native_query"),
            )
            mock_exec_native_query.assert_awaited_once_with("db1", native_query, {})

        self.assertEqual(response.status, 422)
        self.assertEqual(response.headers, {"content-type": "application/json"})
        response_body = json.loads(response.body)
        self.assertEqual(
            response_body["errors"],
            [
                {
                    "name": "UnprocessableError",
                    "detail": "Native query for 'Value' chart must return 'value' field.",
                    "status": 422,
                    "data": {},
                }
            ],
        )

    def test_should_return_error_if_value_query_does_not_return_one_row(self):
        native_query = "select count(*) as not_value from orders;"
        request = Request(
            method=RequestMethod.POST,
            headers={},
            body={"connectionName": "db1", "query": native_query, "type": "Value"},
            client_ip="127.0.0.1",
            query={},
        )
        with patch.object(
            self.datasource_composite,
            "execute_native_query",
            new_callable=AsyncMock,
            return_value=[{"value": 100}, {"value": 100}],
        ) as mock_exec_native_query:
            response = self.loop.run_until_complete(
                self.native_query_resource.dispatch(request, "native_query"),
            )
            mock_exec_native_query.assert_awaited_once_with("db1", native_query, {})

        self.assertEqual(response.status, 422)
        self.assertEqual(response.headers, {"content-type": "application/json"})
        response_body = json.loads(response.body)
        self.assertEqual(
            response_body["errors"],
            [
                {
                    "name": "UnprocessableError",
                    "detail": "Native query for 'Value' chart must return only one row.",
                    "status": 422,
                    "data": {},
                }
            ],
        )

    def test_should_correctly_handle_value_chart_with_previous(self):
        native_query = "select count(*) as value, 0 as previous from orders;"
        request = Request(
            method=RequestMethod.POST,
            headers={},
            body={"connectionName": "db1", "query": native_query, "type": "Value"},
            client_ip="127.0.0.1",
            query={},
        )
        with patch.object(
            self.datasource_composite,
            "execute_native_query",
            new_callable=AsyncMock,
            return_value=[{"value": 100, "previous": 0}],
        ) as mock_exec_native_query:
            response = self.loop.run_until_complete(
                self.native_query_resource.dispatch(request, "native_query"),
            )
            mock_exec_native_query.assert_awaited_once_with("db1", native_query, {})

        self.assertEqual(response.status, 200)
        self.assertEqual(response.headers, {"content-type": "application/json"})
        response_body = json.loads(response.body)
        self.assertIn("id", response_body["data"])
        self.assertEqual(response_body["data"]["type"], "stats")
        self.assertEqual(response_body["data"]["attributes"], {"value": {"countCurrent": 100, "countPrevious": 0}})


class TestNativeQueryResourceLineChart(TestNativeQueryResourceBase):
    def test_should_correctly_handle_line_chart(self):
        native_query = "select count(*) as value, date as key from orders group by date, order by date;"
        request = Request(
            method=RequestMethod.POST,
            headers={},
            body={"connectionName": "db1", "query": native_query, "type": "Line"},
            client_ip="127.0.0.1",
            query={},
        )
        with patch.object(
            self.datasource_composite,
            "execute_native_query",
            new_callable=AsyncMock,
            return_value=[{"key": "2020-01", "value": 100}, {"key": "2020-02", "value": 110}],
        ) as mock_exec_native_query:
            response = self.loop.run_until_complete(
                self.native_query_resource.dispatch(request, "native_query"),
            )
            mock_exec_native_query.assert_awaited_once_with("db1", native_query, {})

        self.assertEqual(response.status, 200)
        self.assertEqual(response.headers, {"content-type": "application/json"})
        response_body = json.loads(response.body)
        self.assertIn("id", response_body["data"])
        self.assertEqual(response_body["data"]["type"], "stats")
        self.assertEqual(
            response_body["data"]["attributes"],
            {"value": [{"label": "2020-01", "values": {"value": 100}}, {"label": "2020-02", "values": {"value": 110}}]},
        )

    def test_should_return_error_if_line_query_return_fields_are_not_good(self):
        native_query = "select count(*) as not_value, date as key from orders group by date, order by date;"
        request = Request(
            method=RequestMethod.POST,
            headers={},
            body={"connectionName": "db1", "query": native_query, "type": "Line"},
            client_ip="127.0.0.1",
            query={},
        )
        with patch.object(
            self.datasource_composite,
            "execute_native_query",
            new_callable=AsyncMock,
            return_value=[{"key": "2020-01", "not_value": 100}, {"key": "2020-02", "not_value": 110}],
        ) as mock_exec_native_query:
            response = self.loop.run_until_complete(
                self.native_query_resource.dispatch(request, "native_query"),
            )
            mock_exec_native_query.assert_awaited_once_with("db1", native_query, {})

        self.assertEqual(response.status, 422)
        self.assertEqual(response.headers, {"content-type": "application/json"})
        response_body = json.loads(response.body)
        self.assertEqual(
            response_body["errors"],
            [
                {
                    "name": "UnprocessableError",
                    "detail": "Native query for 'Line' chart must return 'key' and 'value' fields.",
                    "status": 422,
                    "data": {},
                }
            ],
        )

        native_query = "select count(*) as value, date as not_key from orders group by date, order by date;"
        request.body["query"] = native_query
        with patch.object(
            self.datasource_composite,
            "execute_native_query",
            new_callable=AsyncMock,
            return_value=[{"not_key": "2020-01", "value": 100}, {"not_key": "2020-02", "value": 110}],
        ) as mock_exec_native_query:
            response = self.loop.run_until_complete(
                self.native_query_resource.dispatch(request, "native_query"),
            )
            mock_exec_native_query.assert_awaited_once_with("db1", native_query, {})

        self.assertEqual(response.status, 422)
        self.assertEqual(response.headers, {"content-type": "application/json"})
        response_body = json.loads(response.body)
        self.assertEqual(
            response_body["errors"],
            [
                {
                    "name": "UnprocessableError",
                    "detail": "Native query for 'Line' chart must return 'key' and 'value' fields.",
                    "status": 422,
                    "data": {},
                }
            ],
        )


class TestNativeQueryResourceObjectiveChart(TestNativeQueryResourceBase):
    def test_should_correctly_handle_objective_chart(self):
        native_query = "select count(*) as value, 1000 as objective from orders "
        request = Request(
            method=RequestMethod.POST,
            headers={},
            body={"connectionName": "db1", "query": native_query, "type": "Objective"},
            client_ip="127.0.0.1",
            query={},
        )
        with patch.object(
            self.datasource_composite,
            "execute_native_query",
            new_callable=AsyncMock,
            return_value=[{"value": 150, "objective": 1000}],
        ) as mock_exec_native_query:
            response = self.loop.run_until_complete(
                self.native_query_resource.dispatch(request, "native_query"),
            )
            mock_exec_native_query.assert_awaited_once_with("db1", native_query, {})

        self.assertEqual(response.status, 200)
        self.assertEqual(response.headers, {"content-type": "application/json"})
        response_body = json.loads(response.body)
        self.assertIn("id", response_body["data"])
        self.assertEqual(response_body["data"]["type"], "stats")
        self.assertEqual(response_body["data"]["attributes"], {"value": {"value": 150, "objective": 1000}})

    def test_should_return_error_if_objective_query_return_fields_are_not_good(self):
        native_query = "select count(*) as not_value, 1000 as objective from orders;"
        request = Request(
            method=RequestMethod.POST,
            headers={},
            body={"connectionName": "db1", "query": native_query, "type": "Objective"},
            client_ip="127.0.0.1",
            query={},
        )
        with patch.object(
            self.datasource_composite,
            "execute_native_query",
            new_callable=AsyncMock,
            return_value=[{"not_value": 150, "objective": 1000}],
        ) as mock_exec_native_query:
            response = self.loop.run_until_complete(
                self.native_query_resource.dispatch(request, "native_query"),
            )
            mock_exec_native_query.assert_awaited_once_with("db1", native_query, {})

        self.assertEqual(response.status, 422)
        self.assertEqual(response.headers, {"content-type": "application/json"})
        response_body = json.loads(response.body)
        self.assertEqual(
            response_body["errors"],
            [
                {
                    "name": "UnprocessableError",
                    "detail": "Native query for 'Objective' chart must return 'value' and 'objective' fields.",
                    "status": 422,
                    "data": {},
                }
            ],
        )

        native_query = "select count(*) as value, 1000 as not_objective from orders;"
        request.body["query"] = native_query
        with patch.object(
            self.datasource_composite,
            "execute_native_query",
            new_callable=AsyncMock,
            return_value=[{"value": 150, "not_objective": 1000}],
        ) as mock_exec_native_query:
            response = self.loop.run_until_complete(
                self.native_query_resource.dispatch(request, "native_query"),
            )
            mock_exec_native_query.assert_awaited_once_with("db1", native_query, {})

        self.assertEqual(response.status, 422)
        self.assertEqual(response.headers, {"content-type": "application/json"})
        response_body = json.loads(response.body)
        self.assertEqual(
            response_body["errors"],
            [
                {
                    "name": "UnprocessableError",
                    "detail": "Native query for 'Objective' chart must return 'value' and 'objective' fields.",
                    "status": 422,
                    "data": {},
                }
            ],
        )

    def test_should_return_error_if_objective_query_does_not_return_one_row(self):
        native_query = "select count(*) as value, 1000 as objective from orders;"
        request = Request(
            method=RequestMethod.POST,
            headers={},
            body={"connectionName": "db1", "query": native_query, "type": "Objective"},
            client_ip="127.0.0.1",
            query={},
        )
        with patch.object(
            self.datasource_composite,
            "execute_native_query",
            new_callable=AsyncMock,
            return_value=[{"value": 100, "objective": 1000}, {"value": 100, "objective": 1000}],
        ) as mock_exec_native_query:
            response = self.loop.run_until_complete(
                self.native_query_resource.dispatch(request, "native_query"),
            )
            mock_exec_native_query.assert_awaited_once_with("db1", native_query, {})

        self.assertEqual(response.status, 422)
        self.assertEqual(response.headers, {"content-type": "application/json"})
        response_body = json.loads(response.body)
        self.assertEqual(
            response_body["errors"],
            [
                {
                    "name": "UnprocessableError",
                    "detail": "Native query for 'Objective' chart must return only one row.",
                    "status": 422,
                    "data": {},
                }
            ],
        )


class TestNativeQueryResourceLeaderboardChart(TestNativeQueryResourceBase):
    def test_should_correctly_handle_leaderboard_chart(self):
        native_query = "select sum(score) as value, customer as key from results group by customer order by value desc;"
        request = Request(
            method=RequestMethod.POST,
            headers={},
            body={"connectionName": "db1", "query": native_query, "type": "Leaderboard"},
            client_ip="127.0.0.1",
            query={},
        )
        with patch.object(
            self.datasource_composite,
            "execute_native_query",
            new_callable=AsyncMock,
            return_value=[
                {"value": 150, "key": "Jean"},
                {"value": 140, "key": "Elsa"},
                {"value": 0, "key": "Gautier"},
            ],
        ) as mock_exec_native_query:
            response = self.loop.run_until_complete(
                self.native_query_resource.dispatch(request, "native_query"),
            )
            mock_exec_native_query.assert_awaited_once_with("db1", native_query, {})

        self.assertEqual(response.status, 200)
        self.assertEqual(response.headers, {"content-type": "application/json"})
        response_body = json.loads(response.body)
        self.assertIn("id", response_body["data"])
        self.assertEqual(response_body["data"]["type"], "stats")
        self.assertEqual(
            response_body["data"]["attributes"],
            {"value": [{"key": "Jean", "value": 150}, {"key": "Elsa", "value": 140}, {"key": "Gautier", "value": 0}]},
        )

    def test_should_return_error_if_leaderboard_query_return_fields_are_not_good(self):
        native_query = (
            "select sum(score) as not_value, customer as key from results group by customer order by value desc;"
        )
        request = Request(
            method=RequestMethod.POST,
            headers={},
            body={"connectionName": "db1", "query": native_query, "type": "Leaderboard"},
            client_ip="127.0.0.1",
            query={},
        )
        with patch.object(
            self.datasource_composite,
            "execute_native_query",
            new_callable=AsyncMock,
            return_value=[
                {"not_value": 150, "key": "Jean"},
                {"not_value": 140, "key": "Elsa"},
                {"not_value": 0, "key": "Gautier"},
            ],
        ) as mock_exec_native_query:
            response = self.loop.run_until_complete(
                self.native_query_resource.dispatch(request, "native_query"),
            )
            mock_exec_native_query.assert_awaited_once_with("db1", native_query, {})

        self.assertEqual(response.status, 422)
        self.assertEqual(response.headers, {"content-type": "application/json"})
        response_body = json.loads(response.body)
        self.assertEqual(
            response_body["errors"],
            [
                {
                    "name": "UnprocessableError",
                    "detail": "Native query for 'Leaderboard' chart must return 'key' and 'value' fields.",
                    "status": 422,
                    "data": {},
                }
            ],
        )

        native_query = (
            "select sum(score) as value, customer as not_key from results group by customer order by value desc;"
        )
        request.body["query"] = native_query
        with patch.object(
            self.datasource_composite,
            "execute_native_query",
            new_callable=AsyncMock,
            return_value=[
                {"value": 150, "not_key": "Jean"},
                {"value": 140, "not_key": "Elsa"},
                {"value": 0, "not_key": "Gautier"},
            ],
        ) as mock_exec_native_query:
            response = self.loop.run_until_complete(
                self.native_query_resource.dispatch(request, "native_query"),
            )
            mock_exec_native_query.assert_awaited_once_with("db1", native_query, {})

        self.assertEqual(response.status, 422)
        self.assertEqual(response.headers, {"content-type": "application/json"})
        response_body = json.loads(response.body)
        self.assertEqual(
            response_body["errors"],
            [
                {
                    "name": "UnprocessableError",
                    "detail": "Native query for 'Leaderboard' chart must return 'key' and 'value' fields.",
                    "status": 422,
                    "data": {},
                }
            ],
        )


class TestNativeQueryResourcePieChart(TestNativeQueryResourceBase):
    def test_should_correctly_handle_pie_chart(self):
        native_query = "select count(*) as value, status as key from orders;"
        request = Request(
            method=RequestMethod.POST,
            headers={},
            body={"connectionName": "db1", "query": native_query, "type": "Pie"},
            client_ip="127.0.0.1",
            query={},
        )
        with patch.object(
            self.datasource_composite,
            "execute_native_query",
            new_callable=AsyncMock,
            return_value=[
                {"value": 150, "key": "pending"},
                {"value": 140, "key": "delivering"},
                {"value": 10, "key": "lost"},
            ],
        ) as mock_exec_native_query:
            response = self.loop.run_until_complete(
                self.native_query_resource.dispatch(request, "native_query"),
            )
            mock_exec_native_query.assert_awaited_once_with("db1", native_query, {})

        self.assertEqual(response.status, 200)
        self.assertEqual(response.headers, {"content-type": "application/json"})
        response_body = json.loads(response.body)
        self.assertIn("id", response_body["data"])
        self.assertEqual(response_body["data"]["type"], "stats")
        self.assertEqual(
            response_body["data"]["attributes"],
            {
                "value": [
                    {"value": 150, "key": "pending"},
                    {"value": 140, "key": "delivering"},
                    {"value": 10, "key": "lost"},
                ]
            },
        )

    def test_should_return_error_if_pie_query_return_fields_are_not_good(self):
        native_query = "select count(*) as not_value, status as key from orders;"
        request = Request(
            method=RequestMethod.POST,
            headers={},
            body={"connectionName": "db1", "query": native_query, "type": "Pie"},
            client_ip="127.0.0.1",
            query={},
        )
        with patch.object(
            self.datasource_composite,
            "execute_native_query",
            new_callable=AsyncMock,
            return_value=[
                {"not_value": 150, "key": "pending"},
                {"not_value": 140, "key": "delivering"},
                {"not_value": 10, "key": "lost"},
            ],
        ) as mock_exec_native_query:
            response = self.loop.run_until_complete(
                self.native_query_resource.dispatch(request, "native_query"),
            )
            mock_exec_native_query.assert_awaited_once_with("db1", native_query, {})

        self.assertEqual(response.status, 422)
        self.assertEqual(response.headers, {"content-type": "application/json"})
        response_body = json.loads(response.body)
        self.assertEqual(
            response_body["errors"],
            [
                {
                    "name": "UnprocessableError",
                    "detail": "Native query for 'Pie' chart must return 'key' and 'value' fields.",
                    "status": 422,
                    "data": {},
                }
            ],
        )

        native_query = "select count(*) as value, status as not_key from orders;"
        request.body["query"] = native_query
        with patch.object(
            self.datasource_composite,
            "execute_native_query",
            new_callable=AsyncMock,
            return_value=[
                {"value": 150, "not_key": "pending"},
                {"value": 140, "not_key": "delivering"},
                {"value": 10, "not_key": "lost"},
            ],
        ) as mock_exec_native_query:
            response = self.loop.run_until_complete(
                self.native_query_resource.dispatch(request, "native_query"),
            )
            mock_exec_native_query.assert_awaited_once_with("db1", native_query, {})

        self.assertEqual(response.status, 422)
        self.assertEqual(response.headers, {"content-type": "application/json"})
        response_body = json.loads(response.body)
        self.assertEqual(
            response_body["errors"],
            [
                {
                    "name": "UnprocessableError",
                    "detail": "Native query for 'Pie' chart must return 'key' and 'value' fields.",
                    "status": 422,
                    "data": {},
                }
            ],
        )


class TestNativeQueryResourceVariableConectextVariables(TestNativeQueryResourceBase):

    def test_should_correctly_handle_variable_context(self):
        native_query = "select count(*) as value, status as key from orders where customer = {{recordId}};"
        request = Request(
            method=RequestMethod.POST,
            headers={},
            body={"connectionName": "db1", "query": native_query, "type": "Pie", "contextVariables": {"recordId": 1}},
            client_ip="127.0.0.1",
            query={},
        )
        with patch.object(
            self.datasource_composite,
            "execute_native_query",
            new_callable=AsyncMock,
            return_value=[],
        ) as mock_exec_native_query:
            self.loop.run_until_complete(
                self.native_query_resource.dispatch(request, "native_query"),
            )
            mock_exec_native_query.assert_awaited_once_with(
                "db1",
                "select count(*) as value, status as key from orders where customer = %(recordId)s;",
                {"recordId": 1},
            )

    def test_should_correctly_handle_variable_context_and_like_percent_comparison(self):
        native_query = (
            "select count(*) as value, status as key from orders where customer = {{recordId}} "
            "and customer_name like '%henry%';"
        )
        request = Request(
            method=RequestMethod.POST,
            headers={},
            body={"connectionName": "db1", "query": native_query, "type": "Pie", "contextVariables": {"recordId": 1}},
            client_ip="127.0.0.1",
            query={},
        )
        with patch.object(
            self.datasource_composite,
            "execute_native_query",
            new_callable=AsyncMock,
            return_value=[],
        ) as mock_exec_native_query:
            self.loop.run_until_complete(
                self.native_query_resource.dispatch(request, "native_query"),
            )
            mock_exec_native_query.assert_awaited_once_with(
                "db1",
                "select count(*) as value, status as key from orders where customer = %(recordId)s "
                "and customer_name like '\\%henry\\%';",
                {"recordId": 1},
            )
