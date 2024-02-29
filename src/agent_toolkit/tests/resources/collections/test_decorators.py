import asyncio
import json
from unittest import TestCase
from unittest.mock import AsyncMock, Mock, patch

from forestadmin.agent_toolkit.resources.collections.base_collection_resource import BaseCollectionResource
from forestadmin.agent_toolkit.resources.collections.decorators import (
    _authenticate,
    _authorize,
    _check_method,
    _ip_white_list,
)
from forestadmin.agent_toolkit.resources.collections.requests import RequestCollection
from forestadmin.agent_toolkit.services.permissions.ip_whitelist_service import IpWhiteListService
from forestadmin.agent_toolkit.services.permissions.permission_service import PermissionService
from forestadmin.agent_toolkit.utils.context import RequestMethod
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.exceptions import ForbiddenError
from forestadmin.datasource_toolkit.interfaces.fields import FieldType, Operator, PrimitiveType
from jose import jwt

# how to mock decorators, and why they are not testable :
# https://dev.to/stack-labs/how-to-mock-a-decorator-in-python-55jc


class TestDecorators(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()

        cls.datasource = Datasource()
        Collection.__abstractmethods__ = set()  # to instantiate abstract class
        cls.book_collection = Collection("Book", cls.datasource)
        cls.book_collection.add_fields(
            {
                "id": {
                    "column_type": PrimitiveType.NUMBER,
                    "is_primary_key": True,
                    "type": FieldType.COLUMN,
                    "filter_operators": set([Operator.IN, Operator.EQUAL, Operator.GREATER_THAN]),
                },
                "name": {
                    "column_type": PrimitiveType.STRING,
                    "is_primary_key": False,
                    "type": FieldType.COLUMN,
                    "filter_operators": set([Operator.IN, Operator.EQUAL]),
                },
                "cost": {
                    "column_type": PrimitiveType.NUMBER,
                    "is_primary_key": False,
                    "type": FieldType.COLUMN,
                    "filter_operators": set([Operator.IN, Operator.EQUAL]),
                },
                "categories": {
                    "type": FieldType.ONE_TO_MANY,
                    "origin_key": "category_id",
                    "origin_key_target": "id",
                    "foreign_collection": "Category",
                },
            }
        )
        cls.datasource.add_collection(cls.book_collection)

        cls.permission_service = PermissionService(
            {
                "env_secret": "env_secret",
                "auth_secret": "auth_secret",
                # "server_url": "http://fake.forest.com",
                # "is_production": True,
                # "prefix": "",
                "permission_cache_duration": 180,
            }
        )
        cls.ip_white_list_service = Mock(IpWhiteListService)
        cls.ip_white_list_service.is_enable = AsyncMock(return_value=False)

    def setUp(self):
        self.collection_resource = BaseCollectionResource(
            self.datasource,
            self.permission_service,
            self.ip_white_list_service,
            {
                "env_secret": "env_secret",
                "auth_secret": "auth_secret",
                "server_url": "http://fake.forest.com",
            },
        )


class TestAuthenticateDecorators(TestDecorators):
    def test_should_return_401_if_no_headers(self):
        request = RequestCollection(
            RequestMethod.GET,
            self.book_collection,
            body=None,
            query={},
            headers=None,
        )

        async def _decorated_fn(resource, request):
            pass

        decorated_fn = AsyncMock(wraps=_decorated_fn)

        response = self.loop.run_until_complete(_authenticate(self.collection_resource, request, decorated_fn))

        decorated_fn.assert_not_awaited()
        self.assertEqual(response.status, 401)

    def test_should_return_401_if_authorization_header_is_not_bearer_header(self):
        request = RequestCollection(
            RequestMethod.GET,
            self.book_collection,
            body=None,
            query={},
            headers={"Authorization": "bla bla bla"},
        )

        async def _decorated_fn(resource, request):
            pass

        decorated_fn = AsyncMock(wraps=_decorated_fn)

        response = self.loop.run_until_complete(_authenticate(self.collection_resource, request, decorated_fn))

        decorated_fn.assert_not_awaited()
        self.assertEqual(response.status, 401)

    def test_should_return_401_if_authorization_header_is_not_jwt_encoded(self):
        request = RequestCollection(
            RequestMethod.GET,
            self.book_collection,
            body=None,
            query={},
            headers={"Authorization": "Bearer Wrong_Bearer"},
        )

        async def _decorated_fn(resource, request):
            pass

        decorated_fn = AsyncMock(wraps=_decorated_fn)

        response = self.loop.run_until_complete(_authenticate(self.collection_resource, request, decorated_fn))

        decorated_fn.assert_not_awaited()
        self.assertEqual(response.status, 401)

    def test_should_call_decorated_function_with_user_parsed_into_request(self):
        user = {
            "rendering_id": "1",
            "id": "1",
            "tags": {"test": "tag"},
            "email": "user@company.com",
            "first_name": "first_name",
            "last_name": "last_name",
            "team": "best_team",
        }
        encoded_user = jwt.encode(user, "auth_secret")
        request = RequestCollection(
            RequestMethod.GET,
            self.book_collection,
            body=None,
            query={"timezone": "Europe/Paris"},
            headers={"Authorization": f"Bearer {encoded_user}"},
        )

        async def _decorated_fn(resource, request):
            self.assertEqual(request.user.rendering_id, int(user["rendering_id"]))
            self.assertEqual(request.user.user_id, int(user["id"]))
            self.assertEqual(request.user.tags, user["tags"])
            self.assertEqual(request.user.email, user["email"])
            self.assertEqual(request.user.first_name, user["first_name"])
            self.assertEqual(request.user.last_name, user["last_name"])
            self.assertEqual(request.user.team, user["team"])

            return True

        decorated_fn = AsyncMock(wraps=_decorated_fn)

        response = self.loop.run_until_complete(_authenticate(self.collection_resource, request, decorated_fn))
        decorated_fn.assert_awaited_once_with(self.collection_resource, request)

        self.assertEqual(response, True)

    def test_should_parse_forest_context_url_if_present(self):
        user = {
            "rendering_id": "1",
            "id": "1",
            "tags": {"test": "tag"},
            "email": "user@company.com",
            "first_name": "first_name",
            "last_name": "last_name",
            "team": "best_team",
        }
        encoded_user = jwt.encode(user, "auth_secret")
        request = RequestCollection(
            RequestMethod.GET,
            self.book_collection,
            body=None,
            query={"timezone": "Europe/Paris"},
            headers={
                "Authorization": f"Bearer {encoded_user}",
                "Forest-Context-Url": "http://localhost/?param%3D%2Ftest%2F",
            },
        )

        async def _decorated_fn(resource, request):
            self.assertEqual(request.user.context_url, "http://localhost/?param=/test/")

            return True

        decorated_fn = AsyncMock(wraps=_decorated_fn)
        response = self.loop.run_until_complete(_authenticate(self.collection_resource, request, decorated_fn))
        decorated_fn.assert_awaited_once_with(self.collection_resource, request)

        self.assertEqual(response, True)


class TestAuthorizeDecorators(TestDecorators):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        user = {
            "rendering_id": "1",
            "id": "1",
            "tags": {"test": "tag"},
            "email": "user@company.com",
            "first_name": "first_name",
            "last_name": "last_name",
            "team": "best_team",
        }
        encoded_user = jwt.encode(user, "auth_secret")
        cls.request = RequestCollection(
            RequestMethod.GET,
            cls.book_collection,
            body=None,
            query={"timezone": "Europe/Paris"},
            headers={"Authorization": f"Bearer {encoded_user}"},
        )

    def test_should_raise_if_we_want_chart_and_permission_can_chart_raise(self):
        async def _decorated_fn(resource, request):
            pass

        decorated_fn = AsyncMock(wraps=_decorated_fn)

        with patch.object(
            self.permission_service, "can_chart", new_callable=AsyncMock, side_effect=ForbiddenError("cannot chart")
        ):
            self.assertRaisesRegex(
                ForbiddenError,
                r"cannot chart",
                self.loop.run_until_complete,
                _authorize("chart", self.collection_resource, self.request, decorated_fn),
            )
        decorated_fn.assert_not_awaited()

    def test_should_call_decorated_fn_if_we_want_chart_and_permission_can_chart(self):
        async def _decorated_fn(resource, request):
            self.assertEqual(resource, self.collection_resource)
            self.assertEqual(request, self.request)

        decorated_fn = AsyncMock(wraps=_decorated_fn)

        with patch.object(self.permission_service, "can_chart", new_callable=AsyncMock):
            self.loop.run_until_complete(
                _authorize("chart", self.collection_resource, self.request, decorated_fn),
            )
        decorated_fn.assert_awaited_once_with(self.collection_resource, self.request)

    def test_should_raise_if_we_want_an_action_not_permitted_by_permission_service(self):
        async def _decorated_fn(resource, request):
            pass

        decorated_fn = AsyncMock(wraps=_decorated_fn)

        with patch.object(
            self.permission_service, "can", new_callable=AsyncMock, side_effect=ForbiddenError("cannot browse")
        ):
            self.assertRaisesRegex(
                ForbiddenError,
                r"cannot browse",
                self.loop.run_until_complete,
                _authorize("browse", self.collection_resource, self.request, decorated_fn),
            )
        decorated_fn.assert_not_awaited()

    def test_should_call_decorated_fn_if_we_want_an_action_permitted_by_permission_service(self):
        async def _decorated_fn(resource, request):
            self.assertEqual(resource, self.collection_resource)
            self.assertEqual(request, self.request)

        decorated_fn = AsyncMock(wraps=_decorated_fn)

        with patch.object(self.permission_service, "can", new_callable=AsyncMock):
            self.loop.run_until_complete(_authorize("browse", self.collection_resource, self.request, decorated_fn))
        decorated_fn.assert_awaited_once_with(self.collection_resource, self.request)


class TestCheckMethodDecorators(TestDecorators):
    def test_should_call_the_method_if_the_wanted_method_is_used(self):
        request = RequestCollection(
            RequestMethod.POST,
            self.book_collection,
            body=None,
            query={},
            headers=None,
        )

        async def _decorated_fn(resource, request):
            self.assertEqual(resource, self.collection_resource)
            self.assertEqual(request, request)
            return "bla"

        decorated_fn = AsyncMock(wraps=_decorated_fn)

        response = self.loop.run_until_complete(
            _check_method(RequestMethod.POST, self.collection_resource, request, decorated_fn)
        )
        decorated_fn.assert_awaited_once_with(self.collection_resource, request)
        self.assertEqual(response, "bla")

    def test_should_not_call_the_method_if_the_wanted_method_is_not_used(self):
        request = RequestCollection(
            RequestMethod.POST,
            self.book_collection,
            body=None,
            query={},
            headers=None,
        )

        async def _decorated_fn(resource, request):
            pass

        decorated_fn = AsyncMock(wraps=_decorated_fn)

        response = self.loop.run_until_complete(
            _check_method(RequestMethod.GET, self.collection_resource, request, decorated_fn)
        )
        decorated_fn.assert_not_awaited()
        self.assertEqual(response.status, 405)


class TestIpWhiteList(TestDecorators):
    def test_should_call_check_ip(self):
        request = RequestCollection(
            RequestMethod.POST,
            self.book_collection,
            body=None,
            query={},
            headers=None,
        )

        async def _decorated_fn(resource, request):
            return "OK"

        decorated_fn = AsyncMock(wraps=_decorated_fn)
        with patch.object(self.collection_resource, "check_ip", new_callable=AsyncMock) as check_ip_mock:
            response = self.loop.run_until_complete(_ip_white_list(decorated_fn, self.collection_resource, request))
            check_ip_mock.assert_awaited()
        decorated_fn.assert_awaited()
        self.assertEqual(response, "OK")

    def test_should_not_method_when_check_ip_raise(self):
        request = RequestCollection(
            RequestMethod.POST,
            self.book_collection,
            body=None,
            query={},
            headers=None,
        )

        async def _decorated_fn(resource, request):
            pass

        decorated_fn = AsyncMock(wraps=_decorated_fn)
        with patch.object(
            self.collection_resource,
            "check_ip",
            new_callable=AsyncMock,
            side_effect=ForbiddenError("IP address rejected (127.0.0.1)"),
        ):
            response = self.loop.run_until_complete(_ip_white_list(decorated_fn, self.collection_resource, request))
        decorated_fn.assert_not_awaited()
        self.assertEqual(response.status, 403)
        content_body = json.loads(response.body)
        self.assertEqual(content_body["errors"][0]["name"], "ForbiddenError")
        self.assertEqual(content_body["errors"][0]["detail"], "IP address rejected (127.0.0.1)")
