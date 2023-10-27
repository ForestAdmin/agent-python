import asyncio
import sys
from unittest import TestCase
from unittest.mock import AsyncMock, Mock

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from forestadmin.agent_toolkit.services.permissions.permission_service import PermissionService
from forestadmin.agent_toolkit.utils.context import User
from forestadmin.agent_toolkit.utils.context_variable_injector import ContextVariableInjector
from forestadmin.agent_toolkit.utils.context_variable_instantiator import ContextVariablesInstantiator
from forestadmin.datasource_toolkit.interfaces.fields import Operator
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch import Aggregator, ConditionTreeBranch
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf


class TestContextVariableStack(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()
        cls.user = {
            "rendering_id": "1",
            "id": "1",
            "tags": {"foo": "bar"},
            "email": "dummy@user.fr",
            "first_name": "dummy",
            "last_name": "user",
            "team": "Operations",
        }
        cls.mocked_caller = User(
            rendering_id=1,
            user_id=1,
            tags={"foo": "bar"},
            email="dummy@user.fr",
            first_name="dummy",
            last_name="user",
            team="Operations",
            timezone=zoneinfo.ZoneInfo("Europe/Paris"),
        )

        cls.permission_service = Mock(PermissionService)

    def setUp(self) -> None:
        self.permission_service.get_user_data = AsyncMock(
            return_value={
                "id": 1,
                "firstName": "dummy",
                "lastName": "user",
                "fullName": "dummy user",
                "email": "dummy@user.fr",
                "tags": {"foo": "bar"},
                "roleId": 1,
                "permissionLevel": "admin",
            }
        )
        self.permission_service.get_team = AsyncMock(return_value={"id": 7, "name": "Operations"})

    def test_instantiator_instantiate_context_variable_correctly(self):
        context_variable = self.loop.run_until_complete(
            ContextVariablesInstantiator.build_context_variables(
                self.mocked_caller, {"foo": "bar"}, self.permission_service
            )
        )
        self.permission_service.get_team.assert_awaited_once()
        self.permission_service.get_user_data.assert_awaited_once()
        self.assertEqual(context_variable.request_context_variables, {"foo": "bar"})
        self.assertEqual(context_variable.team, {"id": 7, "name": "Operations"})
        self.assertEqual(
            context_variable.user,
            {
                "id": 1,
                "firstName": "dummy",
                "lastName": "user",
                "fullName": "dummy user",
                "email": "dummy@user.fr",
                "tags": {"foo": "bar"},
                "roleId": 1,
                "permissionLevel": "admin",
            },
        )

    def test_inject_context_in_filter_should_inject_current_users_variables(self):
        request_context_variables = {"custom_variable": "my_best_variable"}
        condition_tree = ConditionTreeBranch(
            Aggregator.OR,
            conditions=[
                ConditionTreeLeaf("id", Operator.EQUAL, "{{currentUser.id}}"),
                ConditionTreeLeaf("team_id", Operator.EQUAL, "{{currentUser.team.id}}"),
                ConditionTreeLeaf("foo_tag", Operator.EQUAL, "{{currentUser.tags.foo}}"),
                ConditionTreeLeaf("front_end_variable", Operator.EQUAL, "{{custom_variable}}"),
            ],
        )
        context_variable = self.loop.run_until_complete(
            ContextVariablesInstantiator.build_context_variables(
                self.mocked_caller, request_context_variables, self.permission_service
            )
        )

        injected_condition_tree = ContextVariableInjector.inject_context_in_filter(condition_tree, context_variable)
        self.assertEqual(injected_condition_tree.conditions[0].value, "1")
        self.assertEqual(injected_condition_tree.conditions[1].value, "7")
        self.assertEqual(injected_condition_tree.conditions[2].value, "bar")
        self.assertEqual(injected_condition_tree.conditions[3].value, "my_best_variable")

    def test_inject_context_in_filter_should_return_null_if_filter_is_null(self):
        context_variable = self.loop.run_until_complete(
            ContextVariablesInstantiator.build_context_variables(self.mocked_caller, {}, self.permission_service)
        )

        injected_condition_tree = ContextVariableInjector.inject_context_in_filter(None, context_variable)
        self.assertIsNone(injected_condition_tree)
