import asyncio
import importlib
import json
import sys
from unittest import TestCase
from unittest.mock import Mock, patch

if sys.version_info < (3, 8):
    from mock import AsyncMock
else:
    from unittest.mock import AsyncMock

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

import forestadmin.agent_toolkit.resources.collections.charts_datasource
from forestadmin.agent_toolkit.options import Options
from forestadmin.agent_toolkit.services.permissions import PermissionService
from forestadmin.agent_toolkit.utils.context import Request, RequestMethod, Response, User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.chart.chart_datasource_decorator import ChartDataSourceDecorator
from forestadmin.datasource_toolkit.interfaces.fields import FieldType, PrimitiveType


def mock_decorator_with_param(*args, **kwargs):
    def decorator(fn):
        def decorated_function(*args, **kwargs):
            return fn(*args, **kwargs)

        return decorated_function

    return decorator


def mock_decorator_no_param(fn):
    def decorated_function(*args, **kwargs):
        return fn(*args, **kwargs)

    return decorated_function


patch("forestadmin.agent_toolkit.resources.collections.decorators.check_method", mock_decorator_with_param).start()
patch("forestadmin.agent_toolkit.resources.collections.decorators.authenticate", mock_decorator_no_param).start()
patch("forestadmin.agent_toolkit.resources.collections.decorators.authorize", mock_decorator_with_param).start()


importlib.reload(forestadmin.agent_toolkit.resources.collections.charts_datasource)
from forestadmin.agent_toolkit.resources.collections.charts_datasource import ChartsDatasourceResource  # noqa: E402


class TestChartDatasourceResource(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()
        cls.permission_service = Mock(PermissionService)
        cls.options = Options(
            auth_secret="fake_secret",
            env_secret="fake_secret",
            server_url="http://fake:5000",
            prefix="forest",
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
        )

    def setUp(self) -> None:
        self.decorated_datasource = ChartDataSourceDecorator(self.datasource)
        self.chart_datasource_resource = ChartsDatasourceResource(
            self.decorated_datasource, self.permission_service, self.options
        )

    def test_dispatch_should_return_400_on_bad_methods(self):
        for method in [RequestMethod.DELETE, RequestMethod.OPTION, RequestMethod.PUT]:
            request = Request(
                method=method,
                query={"chart_name": "test_chart_book"},
                body={},
                headers={},
                user=self.mocked_caller,
            )
            response: Response = self.loop.run_until_complete(self.chart_datasource_resource.dispatch(request, ""))

            response_content = json.loads(response.body)
            assert response.status == 400
            assert response_content["errors"][0] == {
                "name": "ForestException",
                "detail": f"🌳🌳🌳Method {method.value} is not allow for this url.",
                "status": 500,
            }

    def test_dispatch_should_call_handle_api_chart_when_POST(self):
        request = Request(
            method=RequestMethod.POST,
            query={"chart_name": "test_chart_book"},
            body={},
            headers={},
            user=self.mocked_caller,
        )

        with patch.object(
            self.chart_datasource_resource, "handle_api_chart", new_callable=AsyncMock, return_value="Ok"
        ) as mocked_handle_api_chart:
            response: Response = self.loop.run_until_complete(self.chart_datasource_resource.dispatch(request, ""))

            mocked_handle_api_chart.assert_awaited_once()

            assert response.status == 200
            response_content = json.loads(response.body)
            assert response_content == "Ok"

    def test_dispatch_should_call_handle_api_chart_when_GET(self):
        request = Request(
            method=RequestMethod.GET,
            query={"chart_name": "test_chart_book"},
            body=None,
            headers={},
            user=self.mocked_caller,
        )

        with patch.object(
            self.chart_datasource_resource, "handle_smart_chart", new_callable=AsyncMock, return_value="Ok"
        ) as mocked_handle_smart_chart:
            response: Response = self.loop.run_until_complete(self.chart_datasource_resource.dispatch(request, ""))

            mocked_handle_smart_chart.assert_awaited_once()

            assert response.status == 200
            response_content = json.loads(response.body)
            assert response_content == "Ok"

    def test_dispatch_should_return_400_if_chart_method_raise_error(self):
        request = Request(
            method=RequestMethod.GET,
            query={
                "chart_name": "test_chart_book",
            },
            body=None,
            headers={},
            user=self.mocked_caller,
        )

        with patch.object(
            self.chart_datasource_resource,
            "handle_smart_chart",
            new_callable=AsyncMock,
            side_effect=Exception("chart_error"),
        ) as mocked_handle_smart_chart:
            response: Response = self.loop.run_until_complete(self.chart_datasource_resource.dispatch(request, ""))

            mocked_handle_smart_chart.assert_awaited_once()

            assert response.status == 400
            response_content = json.loads(response.body)
            assert response_content["errors"][0] == {
                "name": "Exception",
                "detail": "chart_error",
                "status": 500,
            }

    def test_handle_api_chart_should_call_datasource_render_chart(self):
        request = Request(
            method=RequestMethod.POST,
            query={
                "chart_name": "test_chart_book",
            },
            body={},
            headers={},
            user=self.mocked_caller,
        )

        with patch.object(
            self.decorated_datasource, "render_chart", new_callable=AsyncMock, return_value=100
        ) as mocked_render_chart:
            chart: Response = self.loop.run_until_complete(self.chart_datasource_resource.handle_api_chart(request))

            mocked_render_chart.assert_awaited_once_with(self.mocked_caller, "test_chart_book")
            assert chart["data"].pop("id") is not None
            assert chart == {"data": {"attributes": {"value": 100}, "type": "stats"}}

    def test_handle_smart_chart_should_call_datasource_render_chart(self):
        request = Request(
            method=RequestMethod.GET,
            query={"chart_name": "test_chart_book"},
            headers={},
            user=self.mocked_caller,
        )
        with patch.object(
            self.decorated_datasource, "render_chart", new_callable=AsyncMock, return_value=100
        ) as mocked_render_chart:
            chart: Response = self.loop.run_until_complete(self.chart_datasource_resource.handle_smart_chart(request))

            mocked_render_chart.assert_awaited_once_with(self.mocked_caller, "test_chart_book")
            assert chart == 100
