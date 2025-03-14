import asyncio
import importlib
import json
import sys
from unittest import TestCase
from unittest.mock import AsyncMock, Mock, patch

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

import forestadmin.agent_toolkit.resources.collections.charts_collection
from forestadmin.agent_toolkit.options import Options
from forestadmin.agent_toolkit.resources.collections.requests import RequestCollection, RequestCollectionException
from forestadmin.agent_toolkit.services.permissions.ip_whitelist_service import IpWhiteListService
from forestadmin.agent_toolkit.services.permissions.permission_service import PermissionService
from forestadmin.agent_toolkit.utils.context import Request, RequestMethod, Response, User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.interfaces.fields import FieldType, PrimitiveType


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

importlib.reload(forestadmin.agent_toolkit.resources.collections.charts_collection)
from forestadmin.agent_toolkit.resources.collections.charts_collection import ChartsCollectionResource  # noqa: E402


class TestChartCollectionResource(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()
        cls.permission_service = Mock(PermissionService)
        cls.ip_white_list_service = Mock(IpWhiteListService)
        cls.ip_white_list_service.is_enable = AsyncMock(return_value=False)
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
                "name": {"column_type": PrimitiveType.STRING, "is_primary_key": False, "type": FieldType.COLUMN},
                "cost": {"column_type": PrimitiveType.NUMBER, "is_primary_key": False, "type": FieldType.COLUMN},
            }
        )
        cls.datasource.add_collection(cls.book_collection)
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
        self.chart_collection_resource = ChartsCollectionResource(
            self.datasource, self.permission_service, self.ip_white_list_service, self.options
        )

    def test_dispatch_should_return_400_on_bad_methods(self):
        for method in [RequestMethod.DELETE, RequestMethod.OPTIONS, RequestMethod.PUT]:
            request = Request(
                method=method,
                query={
                    "collection_name": "Book",
                    "chart_name": "test_chart_book",
                },
                body={"record_id": "1"},
                headers={},
                user=self.mocked_caller,
                client_ip="127.0.0.1",
            )
            response: Response = self.loop.run_until_complete(self.chart_collection_resource.dispatch(request, ""))

            response_content = json.loads(response.body)
            assert response.status == 500
            assert response_content["errors"][0] == {
                "name": "ForestException",
                "detail": f"🌳🌳🌳Method {method.value} is not allow for this url.",
                "status": 500,
            }

    def test_dispatch_should_return_400_if_no_collection_supplied(self):
        request = Request(
            method=RequestMethod.POST,
            query={
                # "collection_name": "Book",
                "chart_name": "test_chart_book",
            },
            body={"record_id": "1"},
            headers={},
            user=self.mocked_caller,
            client_ip="127.0.0.1",
        )
        response: Response = self.loop.run_until_complete(self.chart_collection_resource.dispatch(request, ""))

        response_content = json.loads(response.body)
        assert response.status == 500

        assert response_content["errors"][0] == {
            "name": "RequestCollectionException",
            "detail": "🌳🌳🌳'collection_name' is missing in the request",
            "status": 500,
        }

    def test_dispatch_should_call_handle_api_chart_when_POST(self):
        request = Request(
            method=RequestMethod.POST,
            query={
                "collection_name": "Book",
                "chart_name": "test_chart_book",
            },
            body={"record_id": "1"},
            headers={},
            user=self.mocked_caller,
            client_ip="127.0.0.1",
        )

        with patch.object(
            self.chart_collection_resource, "handle_api_chart", new_callable=AsyncMock, return_value="Ok"
        ) as mocked_handle_api_chart:
            response: Response = self.loop.run_until_complete(self.chart_collection_resource.dispatch(request, ""))

            mocked_handle_api_chart.assert_awaited_once()

            assert response.status == 200
            response_content = json.loads(response.body)
            assert response_content == "Ok"

    def test_dispatch_should_call_handle_api_chart_when_GET(self):
        request = Request(
            method=RequestMethod.GET,
            query={
                "collection_name": "Book",
                "chart_name": "test_chart_book",
            },
            body={"record_id": "1"},
            headers={},
            user=self.mocked_caller,
            client_ip="127.0.0.1",
        )

        with patch.object(
            self.chart_collection_resource, "handle_smart_chart", new_callable=AsyncMock, return_value="Ok"
        ) as mocked_handle_smart_chart:
            response: Response = self.loop.run_until_complete(self.chart_collection_resource.dispatch(request, ""))

            mocked_handle_smart_chart.assert_awaited_once()

            assert response.status == 200
            response_content = json.loads(response.body)
            assert response_content == "Ok"

    def test_dispatch_should_return_400_if_chart_method_raise_error(self):
        request = Request(
            method=RequestMethod.GET,
            query={
                "collection_name": "Book",
                "chart_name": "test_chart_book",
            },
            body={"record_id": "1"},
            headers={},
            user=self.mocked_caller,
            client_ip="127.0.0.1",
        )

        with patch.object(
            self.chart_collection_resource,
            "handle_smart_chart",
            new_callable=AsyncMock,
            side_effect=Exception("chart_error"),
        ) as mocked_handle_smart_chart:
            response: Response = self.loop.run_until_complete(self.chart_collection_resource.dispatch(request, ""))

            mocked_handle_smart_chart.assert_awaited_once()

            assert response.status == 500
            response_content = json.loads(response.body)
            assert response_content["errors"][0] == {
                "name": "Exception",
                "detail": "chart_error",
                "status": 500,
            }

    def test_handle_api_chart_should_call_collection_render_chart(self):
        request = Request(
            method=RequestMethod.POST,
            query={
                "collection_name": "Book",
                "chart_name": "test_chart_book",
            },
            body={"record_id": "1"},
            headers={},
            user=self.mocked_caller,
            client_ip="127.0.0.1",
        )
        request_collection = RequestCollection.from_request(request, self.datasource)

        with patch.object(
            self.book_collection, "render_chart", new_callable=AsyncMock, return_value=100
        ) as mocked_render_chart:
            chart: Response = self.loop.run_until_complete(
                self.chart_collection_resource.handle_api_chart(request_collection)
            )

            mocked_render_chart.assert_awaited_once_with(self.mocked_caller, "test_chart_book", [1])
            assert chart["data"].pop("id") is not None
            assert chart == {"data": {"attributes": {"value": 100}, "type": "stats"}}

    def test_handle_smart_chart_should_call_collection_render_chart(self):
        request = Request(
            method=RequestMethod.GET,
            query={"collection_name": "Book", "chart_name": "test_chart_book", "record_id": "1"},
            headers={},
            user=self.mocked_caller,
            client_ip="127.0.0.1",
        )
        request_collection = RequestCollection.from_request(request, self.datasource)

        with patch.object(
            self.book_collection, "render_chart", new_callable=AsyncMock, return_value=100
        ) as mocked_render_chart:
            chart = self.loop.run_until_complete(self.chart_collection_resource.handle_smart_chart(request_collection))

            mocked_render_chart.assert_awaited_once_with(self.mocked_caller, "test_chart_book", [1])
            assert chart == 100

    def test_handle_smart_chart_should_raise_if_no_record_id_is_given(self):
        request = Request(
            method=RequestMethod.GET,
            query={
                "collection_name": "Book",
                "chart_name": "test_chart_book",
            },
            headers={},
            user=self.mocked_caller,
            client_ip="127.0.0.1",
        )
        request_collection = RequestCollection.from_request(request, self.datasource)

        self.assertRaisesRegex(
            RequestCollectionException,
            r"Collection smart chart need a record id in the 'record_id' GET parameter",
            self.loop.run_until_complete,
            self.chart_collection_resource.handle_smart_chart(request_collection),
        )
