import asyncio
import sys
from typing import Any, Coroutine, Dict, Optional, Union
from unittest import TestCase
from unittest.mock import _patch, patch

if sys.version_info < (3, 8):
    from mock import AsyncMock
    from typing_extensions import Literal
else:
    from typing import Literal
    from unittest.mock import AsyncMock


if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from forestadmin.agent_toolkit.resources.collections.requests import RequestCollection
from forestadmin.agent_toolkit.services.permissions.options import RoleOptions
from forestadmin.agent_toolkit.services.permissions.permission_service import PermissionService
from forestadmin.agent_toolkit.utils.context import RequestMethod, User
from forestadmin.agent_toolkit.utils.http import ForestHttpApi
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.action.collections import ActionCollectionDecorator
from forestadmin.datasource_toolkit.decorators.action.context.single import ActionContextSingle
from forestadmin.datasource_toolkit.decorators.action.result_builder import ResultBuilder
from forestadmin.datasource_toolkit.decorators.action.types.actions import ActionSingle
from forestadmin.datasource_toolkit.decorators.datasource_decorator import DatasourceDecorator
from forestadmin.datasource_toolkit.exceptions import ForbiddenError, ForestException
from forestadmin.datasource_toolkit.interfaces.actions import ActionResult
from forestadmin.datasource_toolkit.interfaces.fields import FieldType, Operator, PrimitiveType
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import ConditionTree
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch import Aggregator
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter

MockHttpApiMethods = Union[
    Literal["get_environment_permissions"], Literal["get_users"], Literal["get_rendering_permissions"]
]
MockHttpApiDict = Dict[MockHttpApiMethods, AsyncMock]
PatchHttpApiDict = Dict[MockHttpApiMethods, _patch]


class BaseTestPermissionService(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()
        cls.datasource = Datasource()
        Collection.__abstractmethods__ = set()  # to instantiate abstract class
        cls.booking_collection = Collection("Booking", cls.datasource)
        cls.booking_collection.add_fields(
            {
                "id": {
                    "column_type": PrimitiveType.NUMBER,
                    "is_primary_key": True,
                    "type": FieldType.COLUMN,
                    "is_read_only": False,
                    "validations": [],
                    "default_value": None,
                    "filter_operators": set(),
                    "is_sortable": False,
                    "enum_values": None,
                },
                "title": {
                    "column_type": PrimitiveType.STRING,
                    "is_primary_key": False,
                    "type": FieldType.COLUMN,
                    "is_read_only": False,
                    "validations": [],
                    "default_value": None,
                    "filter_operators": set(),
                    "is_sortable": False,
                    "enum_values": None,
                },
            }
        )
        cls.datasource.add_collection(cls.booking_collection)
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
        cls.options: RoleOptions = {
            "forest_server_url": "https://api.developpement.forestadmin.com",
            "env_secret": "env_secret",
            "prefix": "/forest",
            "is_production": False,
            "permission_cache_duration": 15,
        }
        cls.role_id = 1
        cls.user_role_id = 1

    def setUp(self) -> None:
        self.permission_service = PermissionService(self.options)
        self.datasource_decorator = DatasourceDecorator(self.datasource, ActionCollectionDecorator)
        self.decorated_collection_booking = self.datasource_decorator.get_collection("Booking")

    def mock_forest_http_api(self, scope=None) -> PatchHttpApiDict:
        get_users_patch = patch.object(
            ForestHttpApi,
            "get_users",
            new_callable=AsyncMock,
            return_value=[
                {
                    "id": 1,
                    "firstName": "John",
                    "lastName": "Doe",
                    "fullName": "John Doe",
                    "email": "john.doe@domain.com",
                    "tags": {},
                    "roleId": self.user_role_id,
                    "permissionLevel": "admin",
                },
                {
                    "id": 3,
                    "firstName": "Admin",
                    "lastName": "test",
                    "fullName": "Admin test",
                    "email": "admin@forestadmin.com",
                    "tags": {},
                    "roleId": 13,
                    "permissionLevel": "admin",
                },
            ],
        )

        get_environment_permissions_patch = patch.object(
            ForestHttpApi,
            "get_environment_permissions",
            new_callable=AsyncMock,
            return_value={
                "collections": {
                    "Booking": {
                        "collection": {
                            "browseEnabled": {"roles": [13, self.role_id]},
                            "readEnabled": {"roles": [13, self.role_id]},
                            "editEnabled": {"roles": [13, self.role_id]},
                            "addEnabled": {"roles": [13, self.role_id]},
                            "deleteEnabled": {"roles": [13, self.role_id]},
                            "exportEnabled": {"roles": [13, self.role_id]},
                        },
                        "actions": {
                            "Mark as live": {
                                "triggerEnabled": {"roles": [13, self.role_id]},
                                "triggerConditions": [
                                    {
                                        "filter": {
                                            "aggregator": "and",
                                            "conditions": [
                                                {
                                                    "field": "title",
                                                    "value": None,
                                                    "source": "data",
                                                    "operator": "present",
                                                }
                                            ],
                                        },
                                        "roleId": 15,
                                    }
                                ],
                                "approvalRequired": {"roles": []},
                                "approvalRequiredConditions": {},
                                "userApprovalEnabled": {"roles": [13, self.role_id]},
                                "userApprovalConditions": {},
                                "selfApprovalEnabled": {"roles": [13, self.role_id]},
                            }
                        },
                    }
                }
            },
        )

        get_rendering_permissions_patch = patch.object(
            ForestHttpApi,
            "get_rendering_permissions",
            new_callable=AsyncMock,
            return_value={
                "collections": {"Booking": {"scope": scope, "segments": []}},
                "stats": [
                    {
                        "type": "Pie",
                        "filter": None,
                        "aggregator": "Count",
                        "groupByFieldName": "id",
                        "aggregateFieldName": None,
                        "sourceCollectionName": "Booking",
                    },
                    {
                        "type": "Value",
                        "filter": None,
                        "aggregator": "Count",
                        "aggregateFieldName": None,
                        "sourceCollectionName": "Booking",
                    },
                ],
                "team": {
                    "id": 1,
                    "name": "Operations",
                },
            },
        )

        return {
            "get_environment_permissions": get_environment_permissions_patch,
            "get_users": get_users_patch,
            "get_rendering_permissions": get_rendering_permissions_patch,
        }


class Test01CachePermissionService(BaseTestPermissionService):
    def test_invalidate_cache_should_delete_corresponding_key(self):
        with self.mock_forest_http_api()["get_users"]:
            self.loop.run_until_complete(self.permission_service.get_user_data(1))

        self.assertIsNotNone(self.permission_service.cache["forest.users"])
        self.permission_service.invalidate_cache("forest.users")
        self.assertNotIn("forest.users", self.permission_service.cache)

    def test_dont_call_api_when_something_is_cached(self):
        http_patches: PatchHttpApiDict = self.mock_forest_http_api()
        http_patches: PatchHttpApiDict = self.mock_forest_http_api()
        http_mocks: MockHttpApiDict = {name: patch.start() for name, patch in http_patches.items()}

        response_1 = self.loop.run_until_complete(self.permission_service._get_chart_data(1))
        response_2 = self.loop.run_until_complete(self.permission_service._get_chart_data(1))
        self.assertEqual(response_1, response_2)

        response_1 = self.loop.run_until_complete(self.permission_service.get_user_data(1))
        response_2 = self.loop.run_until_complete(self.permission_service.get_user_data(1))
        self.assertEqual(response_1, response_2)

        response_1 = self.loop.run_until_complete(self.permission_service._get_collection_permissions_data())
        response_2 = self.loop.run_until_complete(self.permission_service._get_collection_permissions_data())
        self.assertEqual(response_1, response_2)

        [mock.assert_awaited_once() for name, mock in http_mocks.items()]

        [patch.stop() for name, patch in http_patches.items()]


class Test02CanPermissionService(BaseTestPermissionService):
    def test_can_should_return_true_in_dev_mode(self):
        with patch.object(
            ForestHttpApi, "get_environment_permissions", new_callable=AsyncMock, return_value=True
        ) as mocked_http_call:
            is_allowed = self.loop.run_until_complete(
                self.permission_service.can(self.mocked_caller, self.booking_collection, "browse")
            )
            mocked_http_call.assert_awaited_once_with(self.options)
        self.assertTrue(is_allowed)

    def test_can_should_return_true_when_user_allowed(self):
        http_patches: PatchHttpApiDict = self.mock_forest_http_api()
        http_mocks: MockHttpApiDict = {name: patch.start() for name, patch in http_patches.items()}

        self.loop.run_until_complete(self.permission_service.can(self.mocked_caller, self.booking_collection, "browse"))
        http_mocks["get_users"].assert_awaited()
        http_mocks["get_environment_permissions"].assert_awaited()
        http_mocks["get_rendering_permissions"].assert_not_awaited()

        [patch.stop() for name, patch in http_patches.items()]

    def test_can_should_call_get_collections_permissions_data_three_times(self):
        """One for "has permissions" and one for permissions which fails, and one for retry"""
        http_patches: PatchHttpApiDict = self.mock_forest_http_api()
        http_patches["get_users"].start()

        mock = {"call_count": 0}

        def mock_get_environment_permissions_patch(options):
            if mock["call_count"] in [0, 1]:
                ret = {
                    "collections": {
                        "Booking": {
                            "collection": {
                                "browseEnabled": {"roles": [1000]},
                                "readEnabled": {"roles": [1000]},
                                "editEnabled": {"roles": [1000]},
                                "addEnabled": {"roles": [1000]},
                                "deleteEnabled": {"roles": [1000]},
                                "exportEnabled": {"roles": [1000]},
                            },
                            "actions": {},
                        }
                    }
                }
            elif mock["call_count"] == 2:
                ret = http_patches["get_environment_permissions"].kwargs["return_value"]
            mock["call_count"] = mock["call_count"] + 1
            return ret

        with patch.object(
            ForestHttpApi,
            "get_environment_permissions",
            new_callable=AsyncMock,
            side_effect=mock_get_environment_permissions_patch,
        ):
            is_allowed = self.loop.run_until_complete(
                self.permission_service.can(self.mocked_caller, self.booking_collection, "browse")
            )
        self.assertTrue(is_allowed)
        self.assertEqual(mock["call_count"], 3)
        http_patches["get_users"].stop()

    def test_can_should_raise_forbidden_error_when_user_is_not_granted(self):
        http_patches: PatchHttpApiDict = self.mock_forest_http_api()
        http_patches["get_users"].start()
        with patch.object(
            ForestHttpApi,
            "get_environment_permissions",
            new_callable=AsyncMock,
            return_value={
                "collections": {
                    "Booking": {
                        "collection": {
                            "browseEnabled": {"roles": [1000]},
                            "readEnabled": {"roles": [1000]},
                            "editEnabled": {"roles": [1000]},
                            "addEnabled": {"roles": [1000]},
                            "deleteEnabled": {"roles": [1000]},
                            "exportEnabled": {"roles": [1000]},
                        },
                        "actions": {},
                    }
                }
            },
        ):
            self.assertRaisesRegex(
                ForbiddenError,
                r"🌳🌳🌳You don't have permission to browse this collection.",
                self.loop.run_until_complete,
                self.permission_service.can(self.mocked_caller, self.booking_collection, "browse"),
            )
        http_patches["get_users"].stop()


class Test03CanChartPermissionService(BaseTestPermissionService):
    def test_can_chart_should_return_true_on_allowed_charts(self):
        http_patches: PatchHttpApiDict = self.mock_forest_http_api()
        rendering_permission_mock: AsyncMock = http_patches["get_rendering_permissions"].start()

        request = RequestCollection(
            method=RequestMethod.POST,
            collection=self.booking_collection,
            body={
                "aggregateFieldName": None,
                "aggregator": "Count",
                "contextVariables": {},
                "filter": None,
                "sourceCollectionName": "Booking",
                "type": "Value",
            },
            user=self.mocked_caller,
        )

        is_allowed = self.loop.run_until_complete(self.permission_service.can_chart(request))
        rendering_permission_mock.assert_awaited_once()
        self.assertTrue(is_allowed)

        http_patches["get_rendering_permissions"].stop()

    def test_can_chart_should_retry_on_not_allowed_at_first_try(self):
        http_patches: PatchHttpApiDict = self.mock_forest_http_api()

        request = RequestCollection(
            method=RequestMethod.POST,
            collection=self.booking_collection,
            body={
                "aggregator": "Count",
                "groupByFieldName": "id",
                "sourceCollectionName": "Booking",
                "type": "Pie",
            },
            user=self.mocked_caller,
        )

        mock = {"call_count": 0}

        def mock_get_rendering_permissions(rendering_id, options):
            if mock["call_count"] == 0:
                ret = {"stats": {}}
            elif mock["call_count"] == 1:
                ret = http_patches["get_rendering_permissions"].kwargs["return_value"]
            mock["call_count"] = mock["call_count"] + 1
            return ret

        with patch.object(
            ForestHttpApi,
            "get_rendering_permissions",
            new_callable=AsyncMock,
            side_effect=mock_get_rendering_permissions,
        ):
            is_allowed = self.loop.run_until_complete(self.permission_service.can_chart(request))
        self.assertTrue(is_allowed)
        self.assertEqual(mock["call_count"], 2)

    def test_can_chart_should_raise_forbidden_error_on_not_allowed_chart(self):
        request = RequestCollection(
            method=RequestMethod.POST,
            collection=self.booking_collection,
            body={
                "aggregator": "Count",
                "groupByFieldName": "registrationNumber",
                "sourceCollectionName": "Car",
                "type": "Pie",
            },
            user=self.mocked_caller,
        )

        with patch.object(
            ForestHttpApi, "get_rendering_permissions", new_callable=AsyncMock, return_value={"stats": {}}
        ):
            self.assertRaisesRegex(
                ForbiddenError,
                r"🌳🌳🌳You don't have permission to access this chart.",
                self.loop.run_until_complete,
                self.permission_service.can_chart(request),
            )


class Test04GetScopePermissionService(BaseTestPermissionService):
    def test_get_scope_should_return_null_when_no_scope_in_permissions(self):
        http_patches: PatchHttpApiDict = self.mock_forest_http_api(None)
        http_patches["get_rendering_permissions"].start()
        http_patches["get_users"].start()

        scope = self.loop.run_until_complete(
            self.permission_service.get_scope(self.mocked_caller, self.booking_collection)
        )

        self.assertIsNone(scope)
        http_patches["get_rendering_permissions"].stop()
        http_patches["get_users"].stop()

    def test_get_scope_should_work_in_simple_cases(self):
        http_patches: PatchHttpApiDict = self.mock_forest_http_api(
            {
                "aggregator": "and",
                "conditions": [
                    {
                        "field": "id",
                        "operator": "greater_than",
                        "value": "1",
                    },
                    {
                        "field": "title",
                        "operator": "present",
                        "value": None,
                    },
                ],
            }
        )

        http_patches["get_rendering_permissions"].start()
        http_patches["get_users"].start()

        scope: ConditionTree = self.loop.run_until_complete(
            self.permission_service.get_scope(self.mocked_caller, self.booking_collection)
        )

        self.assertEqual(scope.aggregator, Aggregator.AND)
        self.assertEqual(scope.conditions[0].field, "id")
        self.assertEqual(scope.conditions[0].operator, Operator.GREATER_THAN)
        self.assertEqual(scope.conditions[0].value, "1")
        self.assertEqual(scope.conditions[1].field, "title")
        self.assertEqual(scope.conditions[1].operator, Operator.PRESENT)
        http_patches["get_rendering_permissions"].stop()
        http_patches["get_users"].stop()

    def test_get_scope_should_work_with_substitutions(self):
        http_patches: PatchHttpApiDict = self.mock_forest_http_api(
            {
                "aggregator": "and",
                "conditions": [
                    {
                        "field": "id",
                        "operator": "equal",
                        "value": "{{currentUser.id}}",
                    },
                ],
            }
        )
        http_patches["get_rendering_permissions"].start()
        http_patches["get_users"].start()

        scope: ConditionTree = self.loop.run_until_complete(
            self.permission_service.get_scope(self.mocked_caller, self.booking_collection)
        )

        self.assertEqual(scope.field, "id")
        self.assertEqual(scope.operator, Operator.EQUAL)
        self.assertEqual(scope.value, "1")
        http_patches["get_rendering_permissions"].stop()
        http_patches["get_users"].stop()


class Test05CanSmartActionPermissionService(BaseTestPermissionService):
    def setUp(self) -> None:
        super().setUp()

        class MarkAsLiveAction(ActionSingle):
            def execute(
                self, context: ActionContextSingle, result_builder: ResultBuilder
            ) -> Coroutine[Any, Any, Optional[ActionResult]]:
                return result_builder.success("success")

        self.decorated_collection_booking.add_action("Mark as live", MarkAsLiveAction())

    def test_can_smart_action_should_return_true_when_user_can_execute_action(self):
        http_patches: PatchHttpApiDict = self.mock_forest_http_api()
        http_patches["get_environment_permissions"].start()
        http_patches["get_users"].start()

        request = RequestCollection(
            method=RequestMethod.POST,
            collection=self.booking_collection,
            query={"action_name": 0, "slug": "mark as live"},
            body={
                "data": {
                    "attributes": {
                        "values": [],
                        "ids": [1],
                        "collection_name": "Booking",
                        "parent_collection_name": None,
                        "parent_collection_id": None,
                        "parent_association_name": None,
                        "all_records": False,
                        "all_records_subset_query": {
                            "fields[Booking]": "id,title",
                            "page[number]": 1,
                            "page[size]": 15,
                            "sort": "-id",
                            "timezone": "Europe/Paris",
                        },
                        "all_records_ids_excluded": [],
                        "smart_action_id": "Booking-Mark@@@as@@@live",
                        "signed_approval_request": None,
                    },
                    "type": "custom-action-requests",
                },
            },
            user=self.mocked_caller,
        )

        with patch.object(self.booking_collection, "aggregate", new_callable=AsyncMock, return_value=[{"value": 1}]):
            is_allowed = self.loop.run_until_complete(
                self.permission_service.can_smart_action(request, self.decorated_collection_booking, Filter({}))
            )

        self.assertTrue(is_allowed)

        http_patches["get_environment_permissions"].stop()
        http_patches["get_users"].stop()

    def test_can_smart_action_should_return_true_when_permission_system_is_deactivated(self):
        request = RequestCollection(
            method=RequestMethod.POST,
            collection=self.booking_collection,
            query={"action_name": 0, "slug": "mark as live"},
            body={
                "data": {
                    "attributes": {
                        "values": {},
                        "ids": [1],
                        "collection_name": "Booking",
                        "parent_collection_name": None,
                        "parent_collection_id": None,
                        "parent_association_name": None,
                        "all_records": False,
                        "all_records_subset_query": {
                            "fields[Booking]": "id,title",
                            "page[number]": 1,
                            "page[size]": 15,
                            "sort": "-id",
                            "timezone": "Europe/Paris",
                        },
                        "all_records_ids_excluded": [],
                        "smart_action_id": "Booking-Mark@@@as@@@live",
                        "signed_approval_request": None,
                    },
                    "type": "custom-action-requests",
                },
            },
            user=self.mocked_caller,
        )

        with patch.object(ForestHttpApi, "get_environment_permissions", new_callable=AsyncMock, return_value=True):
            is_allowed = self.loop.run_until_complete(
                self.permission_service.can_smart_action(request, self.decorated_collection_booking, Filter({}))
            )
        self.assertTrue(is_allowed)

    def test_can_smart_action_should_throw_when_action_is_unknown(self):
        http_patches: PatchHttpApiDict = self.mock_forest_http_api()
        http_patches["get_environment_permissions"].start()
        http_patches["get_users"].start()

        request = RequestCollection(
            method=RequestMethod.POST,
            collection=self.booking_collection,
            query={"action_name": 0, "slug": "fake-smart-action"},
            body={
                "data": {
                    "attributes": {
                        "values": [],
                        "ids": [1],
                        "collection_name": "FakeCollection",
                        "parent_collection_name": None,
                        "parent_collection_id": None,
                        "parent_association_name": None,
                        "all_records": False,
                        "all_records_subset_query": {
                            "fields[Booking]": "id,title",
                            "page[number]": 1,
                            "page[size]": 15,
                            "sort": "-id",
                            "timezone": "Europe/Paris",
                        },
                        "all_records_ids_excluded": [],
                        "smart_action_id": "FakeCollection-fake-smart-action",
                        "signed_approval_request": None,
                    },
                    "type": "custom-action-requests",
                },
            },
            user=self.mocked_caller,
        )

        self.assertRaisesRegex(
            ForestException,
            r"🌳🌳🌳The collection Booking does not have this smart action",
            self.loop.run_until_complete,
            self.permission_service.can_smart_action(request, self.booking_collection, Filter({})),
        )

        http_patches["get_environment_permissions"].stop()
        http_patches["get_users"].stop()
