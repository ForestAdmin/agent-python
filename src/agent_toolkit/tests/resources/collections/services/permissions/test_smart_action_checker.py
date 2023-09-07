import asyncio
import sys
from unittest import TestCase
from unittest.mock import patch

if sys.version_info < (3, 8):
    from mock import AsyncMock
else:
    from unittest.mock import AsyncMock


if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from forestadmin.agent_toolkit.resources.actions.requests import ActionRequest
from forestadmin.agent_toolkit.services.permissions.smart_actions_checker import SmartActionChecker
from forestadmin.agent_toolkit.utils.context import RequestMethod, User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.action.collections import ActionCollectionDecorator
from forestadmin.datasource_toolkit.decorators.datasource_decorator import DatasourceDecorator
from forestadmin.datasource_toolkit.exceptions import ConflictError, ForbiddenError, RequireApproval
from forestadmin.datasource_toolkit.interfaces.fields import FieldType, PrimitiveType
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter


class TestSmartActionChecker(TestCase):
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
        cls.smart_action = {
            "triggerEnabled": {},
            "triggerConditions": {},
            "approvalRequired": {},
            "approvalRequiredConditions": {},
            "userApprovalEnabled": {},
            "userApprovalConditions": {},
            "selfApprovalEnabled": {},
        }

    def setUp(self) -> None:
        self.datasource_decorator = DatasourceDecorator(self.datasource, ActionCollectionDecorator)
        self.decorated_collection_booking = self.datasource_decorator.get_collection("Booking")

    def mk_http_post(self, requester_id=None, all_ids_excluded=None):
        post = {
            "data": {
                "attributes": {
                    "values": {},
                    "ids": {1},
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
                    "all_records_ids_excluded": {},
                    "smart_action_id": "Booking-Mark@@@as@@@live",
                    "signed_approval_request": None,
                },
                "type": "custom-action-requests",
            },
        }
        if requester_id is not None:
            post["data"]["attributes"]["requester_id"] = requester_id
            post["data"]["attributes"]["signed_approval_request"] = "AAABBBCCC"

        if all_ids_excluded is not None:
            post["data"]["attributes"]["all_records"] = True
            post["data"]["attributes"]["all_records_ids_excluded"] = [1, 2, 3]

        return post


class Test01TriggerCanExecuteSmartActionChecker(TestSmartActionChecker):
    def test_should_return_true_when_user_can_trigger_action(self):
        request = ActionRequest(
            method=RequestMethod.POST,
            action_name=0,
            collection=self.decorated_collection_booking,
            body=self.mk_http_post(),
            user=self.mocked_caller,
        )

        smart_action = {**self.smart_action, "triggerEnabled": [1]}

        smart_action_checker = SmartActionChecker(
            request, self.decorated_collection_booking, smart_action, self.mocked_caller, 1, Filter({})
        )

        is_allowed = self.loop.run_until_complete(smart_action_checker.can_execute())
        self.assertTrue(is_allowed)

    def test_should_return_true_when_trigger_conditions_match(self):
        request = ActionRequest(
            method=RequestMethod.POST,
            action_name=0,
            collection=self.decorated_collection_booking,
            body=self.mk_http_post(),
            user=self.mocked_caller,
        )

        smart_action = {
            **self.smart_action,
            "triggerEnabled": [1],
            "triggerConditions": [
                {
                    "filter": {
                        "aggregator": "and",
                        "conditions": [{"field": "title", "value": None, "source": "data", "operator": "present"}],
                    },
                    "role_id": 1,
                }
            ],
        }

        smart_action_checker = SmartActionChecker(
            request, self.decorated_collection_booking, smart_action, self.mocked_caller, 1, Filter({})
        )

        with patch.object(
            self.booking_collection, "aggregate", new_callable=AsyncMock, return_value=[{"value": 1, "group": []}]
        ) as mocked_aggregate:
            is_allowed = self.loop.run_until_complete(smart_action_checker.can_execute())
            mocked_aggregate.assert_awaited()
        self.assertTrue(is_allowed)

    def test_should_return_true_when_trigger_conditions_match_with_all_records_ids_excluded(self):
        request = ActionRequest(
            method=RequestMethod.POST,
            action_name=0,
            collection=self.decorated_collection_booking,
            body=self.mk_http_post(None, True),
            user=self.mocked_caller,
        )
        smart_action = {
            **self.smart_action,
            "triggerEnabled": [1],
            "triggerConditions": [
                {
                    "filter": {
                        "aggregator": "and",
                        "conditions": [{"field": "title", "value": None, "source": "data", "operator": "present"}],
                    },
                    "role_id": 1,
                }
            ],
        }

        smart_action_checker = SmartActionChecker(
            request, self.decorated_collection_booking, smart_action, self.mocked_caller, 1, Filter({})
        )

        with patch.object(
            self.booking_collection, "aggregate", new_callable=AsyncMock, return_value=[{"value": 1, "group": []}]
        ) as mocked_aggregate:
            is_allowed = self.loop.run_until_complete(smart_action_checker.can_execute())
            mocked_aggregate.assert_awaited()
        self.assertTrue(is_allowed)

    def test_should_throw_when_approval_is_required_without_conditions(self):
        request = ActionRequest(
            method=RequestMethod.POST,
            action_name=0,
            collection=self.decorated_collection_booking,
            body=self.mk_http_post(),
            user=self.mocked_caller,
        )
        smart_action = {
            **self.smart_action,
            "triggerEnabled": [1],
            "approvalRequired": [1],
            "approvalRequiredConditions": [],
        }

        smart_action_checker = SmartActionChecker(
            request, self.decorated_collection_booking, smart_action, self.mocked_caller, 1, Filter({})
        )

        self.assertRaisesRegex(
            RequireApproval,
            r"This action requires to be approved",
            self.loop.run_until_complete,
            smart_action_checker.can_execute(),
        )

    def test_should_throw_when_approval_is_required_and_match_conditions(self):
        request = ActionRequest(
            method=RequestMethod.POST,
            action_name=0,
            collection=self.decorated_collection_booking,
            body=self.mk_http_post(),
            user=self.mocked_caller,
        )
        smart_action = {
            **self.smart_action,
            "triggerEnabled": [1],
            "approvalRequired": [1],
            "approvalRequiredConditions": [
                {
                    "filter": {
                        "aggregator": "and",
                        "conditions": [{"field": "id", "value": 1, "source": "data", "operator": "equal"}],
                    },
                    "role_id": 1,
                }
            ],
        }

        smart_action_checker = SmartActionChecker(
            request, self.decorated_collection_booking, smart_action, self.mocked_caller, 1, Filter({})
        )

        with patch.object(
            self.booking_collection, "aggregate", new_callable=AsyncMock, return_value=[{"value": 1, "group": []}]
        ) as mocked_aggregate:
            self.assertRaisesRegex(
                RequireApproval,
                r"This action requires to be approved",
                self.loop.run_until_complete,
                smart_action_checker.can_execute(),
            )
            mocked_aggregate.assert_awaited()

    def test_should_return_ok_when_trigger_with_approval_without_trigger_conditions_and_role_in_approval_required(
        self,
    ):
        request = ActionRequest(
            method=RequestMethod.POST,
            action_name=0,
            collection=self.decorated_collection_booking,
            body=self.mk_http_post(),
            user=self.mocked_caller,
        )
        smart_action = {
            **self.smart_action,
            "triggerEnabled": [1],
            "approvalRequired": [1],
            "approvalRequiredConditions": [
                {
                    "filter": {
                        "aggregator": "and",
                        "conditions": [{"field": "id", "value": 1, "source": "data", "operator": "equal"}],
                    },
                    "role_id": 1,
                }
            ],
        }

        smart_action_checker = SmartActionChecker(
            request, self.decorated_collection_booking, smart_action, self.mocked_caller, 1, Filter({})
        )

        with patch.object(
            self.booking_collection, "aggregate", new_callable=AsyncMock, return_value=[{"value": 0, "group": []}]
        ) as mocked_aggregate:
            is_allowed = self.loop.run_until_complete(smart_action_checker.can_execute())
            mocked_aggregate.assert_awaited()

        self.assertTrue(is_allowed)

    def test_should_return_ok_when_trigger_with_approval_with_trigger_conditions_and_role_in_approval_required(
        self,
    ):
        request = ActionRequest(
            method=RequestMethod.POST,
            action_name=0,
            collection=self.decorated_collection_booking,
            body=self.mk_http_post(),
            user=self.mocked_caller,
        )
        smart_action = {
            **self.smart_action,
            "triggerEnabled": [1],
            "triggerConditions": [
                {
                    "filter": {
                        "aggregator": "and",
                        "conditions": [{"field": "title", "value": None, "source": "data", "operator": "present"}],
                    },
                    "role_id": 1,
                }
            ],
            "approvalRequired": [1],
            "approvalRequiredConditions": [
                {
                    "filter": {
                        "aggregator": "and",
                        "conditions": [{"field": "id", "value": 1, "source": "data", "operator": "equal"}],
                    },
                    "role_id": 1,
                }
            ],
        }

        smart_action_checker = SmartActionChecker(
            request, self.decorated_collection_booking, smart_action, self.mocked_caller, 1, Filter({})
        )

        call_cnt = {"aggregate": 0}

        def mocked_aggregate(self, *args, **kwargs):
            call_cnt["aggregate"] = call_cnt["aggregate"] + 1
            if call_cnt["aggregate"] == 1:
                return [{"value": 0, "group": []}]
            else:
                return [{"value": 1, "group": []}]

        with patch.object(
            self.booking_collection,
            "aggregate",
            new_callable=AsyncMock,
            side_effect=mocked_aggregate,
        ) as mocked_aggregate:
            is_allowed = self.loop.run_until_complete(smart_action_checker.can_execute())
            mocked_aggregate.assert_awaited()

        self.assertTrue(is_allowed)

    def test_should_throw_when_user_role_id_not_in_trigger_enabled_and_approval_required(self):
        request = ActionRequest(
            method=RequestMethod.POST,
            action_name=0,
            collection=self.decorated_collection_booking,
            body=self.mk_http_post(),
            user=self.mocked_caller,
        )
        smart_action = {
            **self.smart_action,
            "triggerEnabled": [1000],
            "approvalRequired": [1000],
        }

        smart_action_checker = SmartActionChecker(
            request, self.decorated_collection_booking, smart_action, self.mocked_caller, 1, Filter({})
        )

        self.assertRaisesRegex(
            ForbiddenError,
            r"You don\'t have the permission to trigger this action",
            self.loop.run_until_complete,
            smart_action_checker.can_execute(),
        )

    def test_should_throw_when_smart_action_does_not_match_with_trigger_conditions_and_approval_required_conditions(
        self,
    ):
        request = ActionRequest(
            method=RequestMethod.POST,
            action_name=0,
            collection=self.decorated_collection_booking,
            body=self.mk_http_post(),
            user=self.mocked_caller,
        )
        smart_action = {
            **self.smart_action,
            "triggerEnabled": [1],
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
                    "roleId": 1,
                },
            ],
            "approvalRequired": [1],
            "approvalRequiredConditions": [
                {
                    "filter": {
                        "aggregator": "and",
                        "conditions": [
                            {
                                "field": "id",
                                "value": 1,
                                "source": "data",
                                "operator": "equal",
                            },
                        ],
                    },
                    "roleId": 1,
                },
            ],
        }

        smart_action_checker = SmartActionChecker(
            request, self.decorated_collection_booking, smart_action, self.mocked_caller, 1, Filter({})
        )

        with patch.object(
            self.booking_collection,
            "aggregate",
            new_callable=AsyncMock,
            return_value=[{"value": 0, "group": []}],
        ):
            self.assertRaisesRegex(
                ForbiddenError,
                r"You don\'t have the permission to trigger this action",
                self.loop.run_until_complete,
                smart_action_checker.can_execute(),
            )

    def test_should_raise_when_with_unknown_operator(self):
        request = ActionRequest(
            method=RequestMethod.POST,
            action_name=0,
            collection=self.decorated_collection_booking,
            body=self.mk_http_post(),
            user=self.mocked_caller,
        )
        smart_action = {
            **self.smart_action,
            "triggerEnabled": [1],
            "triggerConditions": [
                {
                    "filter": {
                        "aggregator": "and",
                        "conditions": [
                            {
                                "field": "title",
                                "value": None,
                                "source": "data",
                                "operator": "unknown",
                            },
                        ],
                    },
                    "roleId": 1,
                },
            ],
        }

        smart_action_checker = SmartActionChecker(
            request, self.decorated_collection_booking, smart_action, self.mocked_caller, 1, Filter({})
        )
        self.assertRaisesRegex(
            ConflictError,
            r"The conditions to trigger this action cannot be verified. Please contact an administrator.",
            self.loop.run_until_complete,
            smart_action_checker.can_execute(),
        )


class Test02ApproveCanExecuteSmartActionChecker(TestSmartActionChecker):
    def test_should_return_true_when_user_can_approve_and_no_approval_conditions_and_requester_id_not_caller(self):
        request = ActionRequest(
            method=RequestMethod.POST,
            action_name=0,
            collection=self.decorated_collection_booking,
            body=self.mk_http_post(20),
            user=self.mocked_caller,
        )

        smart_action = {**self.smart_action, "userApprovalEnabled": [1]}

        smart_action_checker = SmartActionChecker(
            request, self.decorated_collection_booking, smart_action, self.mocked_caller, 1, Filter({})
        )
        is_allowed = self.loop.run_until_complete(smart_action_checker.can_execute())

        self.assertTrue(is_allowed)

    def test_should_return_true_when_user_can_approve_and_no_approval_conditions_and_role_id_in_self_approve(self):
        request = ActionRequest(
            method=RequestMethod.POST,
            action_name=0,
            collection=self.decorated_collection_booking,
            body=self.mk_http_post(1),
            user=self.mocked_caller,
        )

        smart_action = {**self.smart_action, "userApprovalEnabled": [1], "selfApprovalEnabled": [1]}

        smart_action_checker = SmartActionChecker(
            request, self.decorated_collection_booking, smart_action, self.mocked_caller, 1, Filter({})
        )
        is_allowed = self.loop.run_until_complete(smart_action_checker.can_execute())

        self.assertTrue(is_allowed)

    def test_should_return_true_when_user_can_approve_and_approval_conditions_match_and_requester_id_not_caller_id(
        self,
    ):
        request = ActionRequest(
            method=RequestMethod.POST,
            action_name=0,
            collection=self.decorated_collection_booking,
            body=self.mk_http_post(20),
            user=self.mocked_caller,
        )
        smart_action = {
            **self.smart_action,
            "userApprovalEnabled": [1],
            "userApprovalConditions": [
                {
                    "filter": {
                        "aggregator": "and",
                        "conditions": [
                            {
                                "field": "id",
                                "value": 1,
                                "source": "data",
                                "operator": "equal",
                            },
                        ],
                    },
                    "roleId": 1,
                }
            ],
        }
        smart_action_checker = SmartActionChecker(
            request, self.decorated_collection_booking, smart_action, self.mocked_caller, 1, Filter({})
        )

        with patch.object(
            self.booking_collection,
            "aggregate",
            new_callable=AsyncMock,
            return_value=[{"value": 1, "group": []}],
        ):
            self.assertTrue(
                self.loop.run_until_complete(
                    smart_action_checker.can_execute(),
                )
            )

    def test_should_return_true_when_user_can_approve_and_approval_conditions_match_and_role_id_in_self_approve(self):
        request = ActionRequest(
            method=RequestMethod.POST,
            action_name=0,
            collection=self.decorated_collection_booking,
            body=self.mk_http_post(1),
            user=self.mocked_caller,
        )
        smart_action = {
            **self.smart_action,
            "userApprovalEnabled": [1],
            "userApprovalConditions": [
                {
                    "filter": {
                        "aggregator": "and",
                        "conditions": [
                            {
                                "field": "id",
                                "value": 1,
                                "source": "data",
                                "operator": "equal",
                            },
                        ],
                    },
                    "roleId": 1,
                }
            ],
            "selfApprovalEnabled": [1],
        }
        smart_action_checker = SmartActionChecker(
            request, self.decorated_collection_booking, smart_action, self.mocked_caller, 1, Filter({})
        )

        with patch.object(
            self.booking_collection,
            "aggregate",
            new_callable=AsyncMock,
            return_value=[{"value": 1, "group": []}],
        ):
            self.assertTrue(
                self.loop.run_until_complete(
                    smart_action_checker.can_execute(),
                )
            )

    def test_should_raise_when_no_approval_conditions_and_requester_id_is_caller_id(self):
        request = ActionRequest(
            method=RequestMethod.POST,
            action_name=0,
            collection=self.decorated_collection_booking,
            body=self.mk_http_post(1),
            user=self.mocked_caller,
        )
        smart_action = {**self.smart_action}

        smart_action_checker = SmartActionChecker(
            request, self.decorated_collection_booking, smart_action, self.mocked_caller, 1, Filter({})
        )

        self.assertRaisesRegex(
            ForbiddenError,
            r"You don't have the permission to trigger this action",
            self.loop.run_until_complete,
            smart_action_checker.can_execute(),
        )

    def test_should_raise_when_no_approval_conditions_and_role_id_not_in_sel_approved(self):
        request = ActionRequest(
            method=RequestMethod.POST,
            action_name=0,
            collection=self.decorated_collection_booking,
            body=self.mk_http_post(1),
            user=self.mocked_caller,
        )
        smart_action = {**self.smart_action, "selfApprovalEnabled": [1000]}

        smart_action_checker = SmartActionChecker(
            request, self.decorated_collection_booking, smart_action, self.mocked_caller, 1, Filter({})
        )

        self.assertRaisesRegex(
            ForbiddenError,
            r"You don't have the permission to trigger this action",
            self.loop.run_until_complete,
            smart_action_checker.can_execute(),
        )

    def test_should_raise_when_approval_conditions_does_not_match_and_request_id_is_caller_id(self):
        request = ActionRequest(
            method=RequestMethod.POST,
            action_name=0,
            collection=self.decorated_collection_booking,
            body=self.mk_http_post(1),
            user=self.mocked_caller,
        )
        smart_action = {
            **self.smart_action,
            "userApprovalConditions": [
                {
                    "filter": {
                        "aggregator": "and",
                        "conditions": [{"field": "id", "value": 1, "source": "data", "operator": "equal"}],
                    },
                    "role_id": 1,
                }
            ],
        }

        smart_action_checker = SmartActionChecker(
            request, self.decorated_collection_booking, smart_action, self.mocked_caller, 1, Filter({})
        )
        with patch.object(
            self.booking_collection,
            "aggregate",
            new_callable=AsyncMock,
            return_value=[{"value": 1, "group": []}],
        ):
            self.assertRaisesRegex(
                ForbiddenError,
                r"You don't have the permission to trigger this action",
                self.loop.run_until_complete,
                smart_action_checker.can_execute(),
            )

    def test_should_raise_when_approval_conditions_does_not_match_and_request_id_is_not_caller_id(self):
        request = ActionRequest(
            method=RequestMethod.POST,
            action_name=0,
            collection=self.decorated_collection_booking,
            body=self.mk_http_post(20),
            user=self.mocked_caller,
        )
        smart_action = {
            **self.smart_action,
            "userApprovalConditions": [
                {
                    "filter": {
                        "aggregator": "and",
                        "conditions": [{"field": "id", "value": 1000, "source": "data", "operator": "equal"}],
                    },
                    "role_id": 1,
                }
            ],
        }

        smart_action_checker = SmartActionChecker(
            request, self.decorated_collection_booking, smart_action, self.mocked_caller, 1, Filter({})
        )
        with patch.object(
            self.booking_collection,
            "aggregate",
            new_callable=AsyncMock,
            return_value=[{"value": 0, "group": []}],
        ):
            self.assertRaisesRegex(
                ForbiddenError,
                r"You don't have the permission to trigger this action",
                self.loop.run_until_complete,
                smart_action_checker.can_execute(),
            )

    def test_should_raise_when_approval_conditions_does_not_match_and_user_role_id_not_in_self_approve(self):
        request = ActionRequest(
            method=RequestMethod.POST,
            action_name=0,
            collection=self.decorated_collection_booking,
            body=self.mk_http_post(1),
            user=self.mocked_caller,
        )
        smart_action = {
            **self.smart_action,
            "userApprovalConditions": [
                {
                    "filter": {
                        "aggregator": "and",
                        "conditions": [{"field": "id", "value": 1000, "source": "data", "operator": "equal"}],
                    },
                    "role_id": 1,
                }
            ],
        }

        smart_action_checker = SmartActionChecker(
            request, self.decorated_collection_booking, smart_action, self.mocked_caller, 1, Filter({})
        )
        with patch.object(
            self.booking_collection,
            "aggregate",
            new_callable=AsyncMock,
            return_value=[{"value": 0, "group": []}],
        ):
            self.assertRaisesRegex(
                ForbiddenError,
                r"You don't have the permission to trigger this action",
                self.loop.run_until_complete,
                smart_action_checker.can_execute(),
            )
