import asyncio
import copy
import importlib
import json
import sys
from io import StringIO
from unittest import TestCase
from unittest.mock import ANY, AsyncMock, Mock, patch

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

import forestadmin.agent_toolkit.resources.actions.resources
import forestadmin.agent_toolkit.resources.collections.charts_collection
import jwt
from forestadmin.agent_toolkit.forest_logger import ForestLogger
from forestadmin.agent_toolkit.options import Options
from forestadmin.agent_toolkit.resources.actions.requests import ActionRequest
from forestadmin.agent_toolkit.services.permissions.ip_whitelist_service import IpWhiteListService
from forestadmin.agent_toolkit.services.permissions.permission_service import PermissionService
from forestadmin.agent_toolkit.utils.context import Request, RequestMethod, User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.action.collections import ActionCollectionDecorator
from forestadmin.datasource_toolkit.decorators.action.context.single import ActionContextSingle
from forestadmin.datasource_toolkit.decorators.action.result_builder import ResultBuilder
from forestadmin.datasource_toolkit.decorators.action.types.actions import ActionDict
from forestadmin.datasource_toolkit.decorators.datasource_decorator import DatasourceDecorator
from forestadmin.datasource_toolkit.exceptions import ForbiddenError
from forestadmin.datasource_toolkit.interfaces.actions import ActionFieldType, ActionsScope
from forestadmin.datasource_toolkit.interfaces.fields import FieldType, Operator, PrimitiveType
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf


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


importlib.reload(forestadmin.agent_toolkit.resources.actions.resources)
from forestadmin.agent_toolkit.resources.actions.resources import ActionResource  # noqa: E402

# how to mock decorators, and why they are not testable :
# https://dev.to/stack-labs/how-to-mock-a-decorator-in-python-55jc


class BaseTestActionResource(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()
        cls.ip_white_list_service = Mock(IpWhiteListService)
        cls.ip_white_list_service.is_enable = AsyncMock(return_value=False)
        cls.permission_service = Mock(PermissionService)
        cls.permission_service.get_scope = AsyncMock(return_value=None)
        cls.permission_service.can_smart_action = AsyncMock(return_value=True)
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
        cls.category_collection = Collection("Category", cls.datasource)
        cls.category_collection.add_fields(
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
                "user": {
                    "type": FieldType.MANY_TO_ONE,
                    "foreign_key": "category_id",
                    "foreign_key_target": "id",
                    "foreign_collection": "Book",
                },
            }
        )
        cls.datasource.add_collection(cls.category_collection)

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
        self.datasource_decorator = DatasourceDecorator(self.datasource, ActionCollectionDecorator)
        self.decorated_collection_book = self.datasource_decorator.get_collection("Book")
        self.decorated_collection_category = self.datasource_decorator.get_collection("Category")

        self.action_resource = ActionResource(
            self.datasource_decorator, self.permission_service, self.ip_white_list_service, self.options
        )


class TestDispatchActionResource(BaseTestActionResource):
    def setUp(self) -> None:
        async def execute(context: ActionContextSingle, result_builder: ResultBuilder):
            return result_builder.success("Bravo!")

        super().setUp()
        self.test_action: ActionDict = {
            "scope": ActionsScope.SINGLE,
            "execute": execute,
            "form": [
                {
                    "type": ActionFieldType.NUMBER,
                    "label": "Value",
                    "default_value": 0,
                },
            ],
        }
        self.decorated_collection_book.add_action("test_action", self.test_action)

    def test_dispatch_should_return_error_if_no_action_name_specified(self):
        request = Request(
            method=RequestMethod.POST,
            query={
                "timezone": "Europe/Paris",
                "collection_name": "Book",
                # "action_name": 0,
                "slug": "test",
            },
            body={},
            headers={},
            user=None,
            client_ip="127.0.0.1",
        )

        response = self.loop.run_until_complete(self.action_resource.dispatch(request, "execute"))

        content = json.loads(response.body)
        self.assertEqual(response.status, 500)
        self.assertEqual(
            content["errors"][0],
            {
                "name": "RequestActionException",
                "detail": "🌳🌳🌳'action_name' is missing in the request",
                "status": 500,
            },
        )

    def test_should_return_the_return_value_of_hook_when_method_name_is_hook(self):
        request = Request(
            method=RequestMethod.POST,
            query={
                "timezone": "Europe/Paris",
                "collection_name": "Book",
                "action_name": 0,
                "slug": "test_action",
            },
            body={},
            headers={},
            user=None,
            client_ip="127.0.0.1",
        )
        with patch.object(self.action_resource, "hook", new_callable=AsyncMock, return_value="result") as mock_hook:
            response = self.loop.run_until_complete(self.action_resource.dispatch(request, "hook"))
            mock_hook.assert_awaited_once()
        self.assertEqual(response, "result")

    def test_should_return_error_when_hook_method_raise_exception(self):
        request = Request(
            method=RequestMethod.POST,
            query={
                "timezone": "Europe/Paris",
                "collection_name": "Book",
                "action_name": 0,
                "slug": "test_action",
            },
            body={},
            headers={},
            user=None,
            client_ip="127.0.0.1",
        )

        with patch.object(
            self.action_resource, "hook", new_callable=AsyncMock, side_effect=lambda x: 1 / 0
        ) as mock_hook:
            with patch.object(ForestLogger, "log") as mocked_logger:
                response = self.loop.run_until_complete(self.action_resource.dispatch(request, "hook"))
                mocked_logger.assert_called_with("exception", ANY)
            mock_hook.assert_awaited_once()

        content = json.loads(response.body)
        self.assertEqual(response.status, 500)
        self.assertEqual(
            content["errors"][0],
            {"name": "ZeroDivisionError", "detail": "division by zero", "status": 500},
        )

    def test_should_return_the_return_value_of_execute_when_method_name_is_execute(self):
        request = Request(
            method=RequestMethod.POST,
            query={
                "timezone": "Europe/Paris",
                "collection_name": "Book",
                "action_name": 0,
                "slug": "test_action",
            },
            body={},
            headers={},
            user=None,
            client_ip="127.0.0.1",
        )

        with patch.object(self.action_resource, "execute", new_callable=AsyncMock, return_value="result") as mock_hook:
            response = self.loop.run_until_complete(self.action_resource.dispatch(request, "execute"))
            mock_hook.assert_awaited_once()
        self.assertEqual(response, "result")

    def test_should_return_error_when_execute_method_raise_exception(self):
        request = Request(
            method=RequestMethod.POST,
            query={
                "timezone": "Europe/Paris",
                "collection_name": "Book",
                "action_name": 0,
                "slug": "test_action",
            },
            body={},
            headers={},
            user=None,
            client_ip="127.0.0.1",
        )

        with patch.object(
            self.action_resource, "execute", new_callable=AsyncMock, side_effect=lambda x: 1 / 0
        ) as mock_execute:
            with patch.object(ForestLogger, "log") as mocked_logger:
                response = self.loop.run_until_complete(self.action_resource.dispatch(request, "execute"))
                mocked_logger.assert_called_with("exception", ANY)
            mock_execute.assert_awaited_once()

        content = json.loads(response.body)
        self.assertEqual(response.status, 500)
        self.assertEqual(
            content["errors"][0],
            {"name": "ZeroDivisionError", "detail": "division by zero", "status": 500},
        )

    def test_should_return_well_formatted_error_in_case_of_BusinessError(self):
        request = Request(
            method=RequestMethod.POST,
            query={
                "timezone": "Europe/Paris",
                "collection_name": "Book",
                "action_name": 0,
                "slug": "test_action",
            },
            body={},
            headers={},
            user=None,
            client_ip="127.0.0.1",
        )

        with patch.object(
            self.action_resource,
            "execute",
            new_callable=AsyncMock,
            side_effect=ForbiddenError(
                "You don't have the permission to trigger this action.", {}, "CustomActionTriggerForbiddenError", [4]
            ),
        ) as mock_execute:
            with patch.object(ForestLogger, "log") as mocked_logger:
                response = self.loop.run_until_complete(self.action_resource.dispatch(request, "execute"))
                mocked_logger.assert_not_called()

            mock_execute.assert_awaited_once()

        content = json.loads(response.body)
        self.assertEqual(response.status, 403)
        self.assertEqual(
            content["errors"][0],
            {
                "name": "CustomActionTriggerForbiddenError",
                "detail": "You don't have the permission to trigger this action.",
                "status": 403,
                "data": [4],
            },
        )


class TestHookActionResource(BaseTestActionResource):
    def setUp(self) -> None:
        async def execute(context: ActionContextSingle, result_builder: ResultBuilder):
            return result_builder.success("Bravo!")

        super().setUp()
        self.action_form = [
            {
                "type": ActionFieldType.NUMBER,
                "label": "Value",
                "default_value": 0,
            },
            {
                "type": ActionFieldType.STRING,
                "label": "Summary",
                "default_value": "",
                "is_read_only": True,
                "value": lambda ctx: "value is " + str(ctx.form_values.get("Value")),
            },
        ]
        self.test_action_single: ActionDict = {
            "scope": ActionsScope.SINGLE,
            "execute": execute,
            "form": self.action_form,
        }

        self.decorated_collection_book.add_action("test_action_single", self.test_action_single)

    def test_hook_should_raise_if_no_request_body(self):
        request = ActionRequest(
            method=RequestMethod.POST,
            action_name="test_action",
            collection=self.decorated_collection_book,
            body=None,
            query={
                "timezone": "Europe/Paris",
                "collection_name": "Book",
                "action_name": 0,
                "slug": "test_action_single",
            },
            headers={},
            user=self.mocked_caller,
            client_ip="127.0.0.1",
        )
        self.assertRaisesRegex(Exception, "", self.loop.run_until_complete, self.action_resource.hook(request))

    def test_hook_should_compute_form_and_return_it_with_all_condition_tree_parsing(self):
        async def execute(context: ActionContextSingle, result_builder: ResultBuilder):
            return result_builder.success("Bravo!")

        self.decorated_collection_book.add_action(
            "test_action_bulk", {"scope": ActionsScope.BULK, "form": self.action_form, "execute": execute}
        )
        request = ActionRequest(
            method=RequestMethod.POST,
            action_name="test_action_bulk",
            collection=self.decorated_collection_book,
            body={
                "data": {
                    "attributes": {
                        "fields": [
                            {
                                "field": "Value",
                                "type": "Number",
                                "reference": None,
                                "enums": None,
                                "description": "",
                                "isRequired": False,
                                "value": 5,
                                "previousValue": 0,
                                "widgetEdit": {"name": "number input", "parameters": {}},
                                "isReadOnly": False,
                                "hook": "changeHook",
                            },
                            {
                                "field": "Summary",
                                "type": "String",
                                "reference": None,
                                "enums": None,
                                "description": "",
                                "isRequired": False,
                                "value": "",
                                "previousValue": "",
                                "widgetEdit": {"name": "'text editor'", "parameters": {"placeholder": None}},
                                "isReadOnly": True,
                                "hook": None,
                            },
                        ],
                        "changed_field": "Value",
                        "ids": ["10", "11"],
                        "collection_name": "Category",
                        "parent_collection_name": "Book",
                        "parent_collection_id": "1",
                        "parent_association_name": "categories",
                        "all_records": True,
                        "all_records_subset_query": {
                            "fields[Book]": "id,name,cost",
                            "page[number]": 1,
                            "page[size]": 15,
                            "sort": "-id",
                            "timezone": "Europe/Paris",
                            "filters": '{"field":"id","operator":"greater_than","value":-1}',
                        },
                        "all_records_ids_excluded": ["8", "9"],
                        "smart_action_id": "Book-test_action",
                        "signed_approval_requests": None,
                    },
                    "type": "custom-action-hook-requests",
                }
            },
            query={
                "timezone": "Europe/Paris",
                "collection_name": "Book",
                "action_name": "1",
                "slug": "test_action_bulk",
            },
            headers={},
            user=self.mocked_caller,
            client_ip="127.0.0.1",
        )

        with patch.object(
            self.permission_service,
            "get_scope",
            new_callable=AsyncMock,
            return_value=ConditionTreeLeaf(field="id", operator=Operator.GREATER_THAN, value=-2),
        ):
            response = self.loop.run_until_complete(self.action_resource.hook(request))
        self.assertEqual(response.status, 200)
        content = json.loads(response.body)
        self.assertEqual(
            content["fields"],
            [
                {
                    "field": "Value",
                    "label": "Value",
                    "value": 5,
                    "defaultValue": 0,
                    "description": "",
                    "enums": None,
                    "hook": "changeHook",
                    "isReadOnly": False,
                    "isRequired": False,
                    "reference": None,
                    "type": "Number",
                    "widgetEdit": None,
                },
                {
                    "field": "Summary",
                    "label": "Summary",
                    "value": "value is 5",
                    "defaultValue": "",
                    "description": "",
                    "enums": None,
                    "hook": None,
                    "isReadOnly": True,
                    "isRequired": False,
                    "reference": None,
                    "type": "String",
                    "widgetEdit": None,
                },
            ],
        )
        self.assertEqual(
            content["layout"],
            [{"component": "input", "fieldId": "Value"}, {"component": "input", "fieldId": "Summary"}],
        )

    def test_hook_should_return_layout_if_it_is_set(self):
        test_action_single: ActionDict = {
            "scope": "Global",
            "execute": lambda ctx, result_builder: result_builder.success(),
            "form": [
                {"type": "String", "label": "firstname"},
                {"type": "Layout", "component": "Separator", "if_": lambda ctx: True},
                {"type": "String", "label": "lastname", "if_": lambda ctx: True},
            ],
        }

        self.decorated_collection_book.add_action("test_action_with_layout", test_action_single)

        request = ActionRequest(
            method=RequestMethod.POST,
            action_name="test_action_with_layout",
            collection=self.decorated_collection_book,
            query={
                "timezone": "Europe/Paris",
                "collection_name": "Book",
                "action_name": "2",
                "slug": "test_action_with_layout",
            },
            headers={},
            user=self.mocked_caller,
            body={
                "data": {
                    "attributes": {
                        "ids": [],
                        "collection_name": "Book",
                        "parent_collection_name": None,
                        "parent_collection_id": None,
                        "parent_association_name": None,
                        "all_records": False,
                        "all_records_subset_query": {
                            "fields[Book]": "id,name,cost",
                            "page[number]": 1,
                            "page[size]": 15,
                            "sort": "-id",
                            "timezone": "Europe/Paris",
                            "filters": '{"field":"id","operator":"greater_than","value":-1}',
                        },
                        "all_records_ids_excluded": [],
                        "smart_action_id": "Book-test_action_with_layout",
                        "signed_approval_request": None,
                    },
                    "type": "action-requests",
                }
            },
            client_ip="127.0.0.1",
        )

        with patch.object(
            self.permission_service,
            "get_scope",
            new_callable=AsyncMock,
            return_value=ConditionTreeLeaf(field="id", operator=Operator.GREATER_THAN, value=-2),
        ):
            response = self.loop.run_until_complete(self.action_resource.hook(request))
        self.assertEqual(response.status, 200)
        content = json.loads(response.body)
        self.assertEqual(
            content["fields"],
            [
                {
                    "field": "firstname",
                    "label": "firstname",
                    "value": None,
                    "defaultValue": None,
                    "description": "",
                    "enums": None,
                    "hook": None,
                    "isReadOnly": False,
                    "isRequired": False,
                    "reference": None,
                    "type": "String",
                    "widgetEdit": None,
                },
                {
                    "field": "lastname",
                    "label": "lastname",
                    "value": None,
                    "defaultValue": None,
                    "description": "",
                    "enums": None,
                    "hook": None,
                    "isReadOnly": False,
                    "isRequired": False,
                    "reference": None,
                    "type": "String",
                    "widgetEdit": None,
                },
            ],
        )
        self.assertEqual(
            content["layout"],
            [
                {"component": "input", "fieldId": "firstname"},
                {"component": "separator"},
                {"component": "input", "fieldId": "lastname"},
            ],
        )


class TestExecuteActionResource(BaseTestActionResource):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.body_params = {
            "data": {
                "attributes": {
                    "values": {},
                    "ids": [],
                    "collection_name": "Book",
                    "parent_collection_name": None,
                    "parent_collection_id": None,
                    "parent_association_name": None,
                    "all_records": False,
                    "all_records_subset_query": {
                        "fields[Book]": "id,name,cost",
                        "page[number]": 1,
                        "page[size]": 15,
                        "sort": "-id",
                        "timezone": "Europe/Paris",
                    },
                    "all_records_ids_excluded": [],
                    "smart_action_id": "Book-test_action_global",
                    "signed_approval_requests": None,
                },
                "type": "custom-action-requests",
            }
        }

    def test_execute_should_raise_if_no_request_body(self):
        self.decorated_collection_book.add_action(
            "test_action_global", {"scope": ActionsScope.GLOBAL, "execute": lambda ctx, rb: rb.success()}
        )
        request = ActionRequest(
            method=RequestMethod.POST,
            action_name="test_action_global",
            collection=self.decorated_collection_book,
            body=None,
            query={
                "timezone": "Europe/Paris",
                "collection_name": "Book",
                "action_name": 0,
                "slug": "test_action_global",
            },
            headers={},
            user=self.mocked_caller,
            client_ip="127.0.0.1",
        )
        self.assertRaisesRegex(Exception, "", self.loop.run_until_complete, self.action_resource.execute(request))

    def test_execute_should_execute_on_collection(self):
        self.decorated_collection_book.add_action(
            "test_action_global", {"scope": ActionsScope.GLOBAL, "execute": lambda ctx, rb: rb.success()}
        )
        request = ActionRequest(
            method=RequestMethod.POST,
            action_name="test_action_global",
            collection=self.decorated_collection_book,
            body=self.body_params,
            query={
                "timezone": "Europe/Paris",
                "collection_name": "Book",
                "action_name": 0,
                "slug": "test_action_global",
            },
            headers={},
            user=self.mocked_caller,
            client_ip="127.0.0.1",
        )

        with patch.object(
            self.decorated_collection_book,
            "execute",
            new_callable=AsyncMock,
            return_value=ResultBuilder().success("bravo"),
        ) as mocked_execute:
            response = self.loop.run_until_complete(self.action_resource.execute(request))
            mocked_execute.assert_awaited_once_with(
                self.mocked_caller,
                "test_action_global",
                {},
                ANY,
            )
        self.assertEqual(response.status, 200)
        self.assertEqual(response.body, '{"success": "bravo"}')

    def test_execute_should_return_correctly_formatted_error_on_error_response(self):
        self.decorated_collection_book.add_action(
            "test_action_global", {"scope": ActionsScope.GLOBAL, "execute": lambda ctx, rb: rb.error("error message")}
        )
        request = ActionRequest(
            method=RequestMethod.POST,
            action_name="test_action_global",
            collection=self.decorated_collection_book,
            body=self.body_params,
            query={
                "timezone": "Europe/Paris",
                "collection_name": "Book",
                "action_name": 0,
                "slug": "test_action_global",
            },
            headers={},
            user=self.mocked_caller,
            client_ip="127.0.0.1",
        )
        response = self.loop.run_until_complete(self.action_resource.execute(request))
        self.assertEqual(response.status, 400)
        self.assertEqual(response.body, '{"error": "error message"}')

    def test_execute_should_return_correctly_formatted_html_error_on_error_response(self):
        self.decorated_collection_book.add_action(
            "test_error_html",
            {
                "scope": ActionsScope.GLOBAL,
                "execute": lambda ctx, rb: rb.error("<b>error message</b>", {"type": "html"}),
            },
        )
        request = ActionRequest(
            method=RequestMethod.POST,
            action_name="test_error_html",
            collection=self.decorated_collection_book,
            body=self.body_params,
            query={
                "timezone": "Europe/Paris",
                "collection_name": "Book",
                "action_name": 0,
                "slug": "test_error_html",
            },
            headers={},
            user=self.mocked_caller,
            client_ip="127.0.0.1",
        )
        response = self.loop.run_until_complete(self.action_resource.execute(request))
        self.assertEqual(response.status, 400)
        self.assertEqual(response.body, '{"html": "<b>error message</b>"}')

    def test_execute_should_return_correctly_formatted_success_on_success_response(self):
        self.decorated_collection_book.add_action(
            "test_action_global",
            {
                "scope": ActionsScope.GLOBAL,
                "execute": lambda ctx, rb: rb.success("<h1>success message</h1>", {"type": "html"}),
            },
        )
        request = ActionRequest(
            method=RequestMethod.POST,
            action_name="test_action_global",
            collection=self.decorated_collection_book,
            body=self.body_params,
            query={
                "timezone": "Europe/Paris",
                "collection_name": "Book",
                "action_name": 0,
                "slug": "test_action_global",
            },
            headers={},
            user=self.mocked_caller,
            client_ip="127.0.0.1",
        )
        response = self.loop.run_until_complete(self.action_resource.execute(request))
        self.assertEqual(response.status, 200)
        self.assertEqual(response.body, '{"html": "<h1>success message</h1>"}')

    def test_execute_should_return_correctly_formatted_webhook_on_webhook_response(self):
        self.decorated_collection_book.add_action(
            "test_action_global",
            {
                "scope": ActionsScope.GLOBAL,
                "execute": lambda ctx, rb: rb.webhook("http://webhook.com/"),
            },
        )
        request = ActionRequest(
            method=RequestMethod.POST,
            action_name="test_action_global",
            collection=self.decorated_collection_book,
            body=self.body_params,
            query={
                "timezone": "Europe/Paris",
                "collection_name": "Book",
                "action_name": 0,
                "slug": "test_action_global",
            },
            headers={},
            user=self.mocked_caller,
            client_ip="127.0.0.1",
        )
        response = self.loop.run_until_complete(self.action_resource.execute(request))
        self.assertEqual(response.status, 200)
        self.assertEqual(
            response.body,
            '{"webhook": {"url": "http://webhook.com/", "method": "POST", "headers": {}, "body": {}}}',
        )

    def test_execute_should_return_correctly_formatted_file_on_file_response(self):
        self.decorated_collection_book.add_action(
            "test_action_global",
            {
                "scope": ActionsScope.GLOBAL,
                "execute": lambda ctx, rb: rb.file(StringIO("bla bla"), "testFile.txt", "text/plain;charset=UTF-8"),
            },
        )
        request = ActionRequest(
            method=RequestMethod.POST,
            action_name="test_action_global",
            collection=self.decorated_collection_book,
            body=self.body_params,
            query={
                "timezone": "Europe/Paris",
                "collection_name": "Book",
                "action_name": "0",
                "slug": "test_action_global",
            },
            headers={},
            user=self.mocked_caller,
            client_ip="127.0.0.1",
        )
        response = self.loop.run_until_complete(self.action_resource.execute(request))
        self.assertEqual(response.name, "testFile.txt")
        self.assertEqual(response.mimetype, "text/plain;charset=UTF-8")
        self.assertEqual(response.file.read(), "bla bla")
        self.assertIn(("Access-Control-Expose-Headers", "Content-Disposition"), response.headers.items())

    def test_execute_should_return_correctly_formatted_redirect_on_redirect_response(self):
        self.decorated_collection_book.add_action(
            "test_action_global",
            {"scope": ActionsScope.GLOBAL, "execute": lambda ctx, rb: rb.redirect("/path/to/redirect")},
        )
        request = ActionRequest(
            method=RequestMethod.POST,
            action_name="test_action_global",
            collection=self.decorated_collection_book,
            body=self.body_params,
            query={
                "timezone": "Europe/Paris",
                "collection_name": "Book",
                "action_name": "0",
                "slug": "test_action_global",
            },
            headers={},
            user=self.mocked_caller,
            client_ip="127.0.0.1",
        )
        response = self.loop.run_until_complete(self.action_resource.execute(request))
        self.assertEqual(response.status, 200)
        self.assertEqual(response.body, '{"redirectTo": "/path/to/redirect"}')

    def test_execute_should_return_success_on_none_response(self):
        self.decorated_collection_book.add_action(
            "test_action_global", {"scope": ActionsScope.GLOBAL, "execute": lambda ctx, rb: None}
        )
        request = ActionRequest(
            method=RequestMethod.POST,
            action_name="test_action_global",
            collection=self.decorated_collection_book,
            body=self.body_params,
            query={
                "timezone": "Europe/Paris",
                "collection_name": "Book",
                "action_name": "0",
                "slug": "test_action_global",
            },
            headers={},
            user=self.mocked_caller,
            client_ip="127.0.0.1",
        )
        response = self.loop.run_until_complete(self.action_resource.execute(request))
        self.assertEqual(response.status, 200)
        self.assertEqual(response.body, '{"success": "Success"}')

    def test_execute_should_update_body_attributes_on_approval(self):
        self.decorated_collection_book.add_action(
            "test_action_global", {"scope": ActionsScope.GLOBAL, "execute": lambda ctx, rb: rb.success()}
        )
        request = ActionRequest(
            method=RequestMethod.POST,
            action_name="test_action_global",
            collection=self.decorated_collection_book,
            body={
                "data": {
                    "attributes": {
                        "values": {},
                        "ids": [],
                        "collection_name": "Wrong_collection",
                        "parent_collection_name": None,
                        "parent_collection_id": None,
                        "parent_association_name": None,
                        "all_records": True,
                        "all_records_subset_query": {
                            "fields[Book]": "id,name,cost",
                            "page[number]": 1,
                            "page[size]": 15,
                            "sort": "-id",
                            "timezone": "Europe/Berlin",
                        },
                        "all_records_ids_excluded": [1, 2],
                        "smart_action_id": "Book-test_action_global",
                        "signed_approval_request": jwt.encode(self.body_params, self.options["env_secret"]),
                    },
                    "type": "custom-action-requests",
                }
            },
            query={
                "timezone": "Europe/Paris",
                "collection_name": "Book",
                "action_name": 0,
                "slug": "test_action_global",
            },
            headers={},
            user=self.mocked_caller,
            client_ip="127.0.0.1",
        )

        with patch.object(
            self.action_resource,
            "_get_records_selection",
            new_callable=AsyncMock,
            wraps=self.action_resource._get_records_selection,
        ) as mocked_get_records_selection:
            self.loop.run_until_complete(self.action_resource.execute(request))
            mocked_get_records_selection.assert_awaited_once()
            request_arg_body = mocked_get_records_selection.await_args.args[0].body
        self.assertEqual(request_arg_body["data"]["attributes"]["collection_name"], "Book")
        self.assertEqual(request_arg_body["data"]["attributes"]["all_records"], False)
        self.assertEqual(request_arg_body["data"]["attributes"]["all_records_ids_excluded"], [])
        self.assertEqual(request_arg_body["data"]["attributes"]["all_records_subset_query"]["timezone"], "Europe/Paris")
        self.assertIsNotNone(request_arg_body["data"]["attributes"]["signed_approval_request"])

    def test_execute_should_handle_response_headers(self):
        def execute(ctx, result_builder):
            result_builder.set_header("headerOne", "valueOne")
            return result_builder.success()

        self.decorated_collection_book.add_action(
            "test_action_global", {"scope": ActionsScope.GLOBAL, "execute": execute}
        )

        request = ActionRequest(
            method=RequestMethod.POST,
            action_name="test_action_global",
            collection=self.decorated_collection_book,
            body=self.body_params,
            query={
                "timezone": "Europe/Paris",
                "collection_name": "Book",
                "action_name": "0",
                "slug": "test_action_global",
            },
            headers={},
            user=self.mocked_caller,
            client_ip="127.0.0.1",
        )
        response = self.loop.run_until_complete(self.action_resource.execute(request))
        self.assertEqual(response.headers["headerOne"], "valueOne")
        self.assertEqual(response.headers["headerOne"], "valueOne")

    def test_execute_should_get_all_form_fields_included_hidden(self):

        self.decorated_collection_book.add_action(
            "test_action_global_hidden_fields",
            {
                "scope": ActionsScope.GLOBAL,
                "execute": lambda ctx, rb: rb.success(ctx.form_values.get("hidden_field")),
                "form": [
                    {
                        "type": "String",
                        "label": "hidden_field",
                        "if_": lambda ctx: False,
                    }
                ],
            },
        )
        body_params = copy.deepcopy(self.body_params)
        body_params["data"]["attributes"]["values"] = {"hidden_field": "hidden_value"}
        request = ActionRequest(
            method=RequestMethod.POST,
            action_name="test_action_global_hidden_fields",
            collection=self.decorated_collection_book,
            body=body_params,
            query={
                "timezone": "Europe/Paris",
                "collection_name": "Book",
                "action_name": 0,
                "slug": "test_action_global_hidden_fields",
            },
            headers={},
            user=self.mocked_caller,
            client_ip="127.0.0.1",
        )
        with patch.object(
            self.decorated_collection_book,
            "get_form",
            new_callable=AsyncMock,
            wraps=self.decorated_collection_book.get_form,
        ) as spy_get_form:
            response = self.loop.run_until_complete(self.action_resource.execute(request))
            spy_get_form.assert_awaited_once_with(
                request.user,
                "test_action_global_hidden_fields",
                {"hidden_field": "hidden_value"},
                ANY,
                {"include_hidden_fields": True},
            )
        self.assertEqual(response.status, 200)
        self.assertEqual(
            response.body,
            '{"success": "hidden_value"}',
        )
