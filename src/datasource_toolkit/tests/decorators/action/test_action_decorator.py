import asyncio
import sys
from typing import Any, Coroutine, Union
from unittest import TestCase

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.action.collections import ActionCollectionDecorator
from forestadmin.datasource_toolkit.decorators.action.context.single import ActionContextSingle
from forestadmin.datasource_toolkit.decorators.action.result_builder import ResultBuilder
from forestadmin.datasource_toolkit.decorators.action.types.actions import ActionSingle
from forestadmin.datasource_toolkit.decorators.action.types.fields import (
    PlainEnumDynamicField,
    PlainNumberDynamicField,
    PlainStringDynamicField,
)
from forestadmin.datasource_toolkit.decorators.datasource_decorator import DatasourceDecorator
from forestadmin.datasource_toolkit.exceptions import ForestException
from forestadmin.datasource_toolkit.interfaces.actions import ActionField, ActionFieldType, ActionResult, ActionsScope


class TestActionCollectionCustomizer(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()
        cls.datasource: Datasource = Datasource()
        Collection.__abstractmethods__ = set()  # to instantiate abstract class

        cls.collection_product = Collection("Product", cls.datasource)
        cls.datasource.add_collection(cls.collection_product)

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
        class SingleAction(ActionSingle):
            SCOPE = ActionsScope.SINGLE
            FORM = [PlainNumberDynamicField(label="amount", type=ActionFieldType.NUMBER)]

            async def execute(
                self, context: ActionContextSingle, result_builder: ResultBuilder
            ) -> Coroutine[Any, Any, Union[ActionResult, None]]:
                return result_builder.success("Bravo !!!")

        self.ActionSingle = SingleAction

        self.datasource_decorator = DatasourceDecorator(self.datasource, ActionCollectionDecorator)
        self.product_collection = self.datasource_decorator.get_collection("Product")

    def test_add_action_should_add_action_in_actions_list(self):
        self.product_collection.add_action("action_test", self.ActionSingle())

        assert "action_test" in self.product_collection.schema["actions"]

    def test_execute_should_return_success_response(self):
        self.product_collection.add_action("action_test", self.ActionSingle())

        result = self.loop.run_until_complete(self.product_collection.execute(self.mocked_caller, "action_test", {}))

        assert result == {
            "type": "Success",
            "message": "Bravo !!!",
            "format": "text",
            # "refresh": {
            #     "relationships": {},
            # },
            # "html": None,
            "invalidated": set(),
        }

    def test_execute_return_default_response_when_result_is_not_result_builder_response(self):
        class TestAction(ActionSingle):
            SCOPE = ActionsScope.SINGLE
            FORM = [PlainNumberDynamicField(label="amount", type=ActionFieldType.NUMBER)]

            async def execute(
                self, context: ActionContextSingle, result_builder: ResultBuilder
            ) -> Coroutine[Any, Any, Union[ActionResult, None]]:
                return None

        self.product_collection.add_action("action_test", TestAction())

        result = self.loop.run_until_complete(self.product_collection.execute(self.mocked_caller, "action_test", {}))
        assert result == {"type": "Success", "invalidated": set(), "format": "text", "message": "Success"}

    def test_execute_return_correct_response_builder(self):
        class TestAction(ActionSingle):
            SCOPE = ActionsScope.SINGLE
            FORM = [PlainNumberDynamicField(label="amount", type=ActionFieldType.NUMBER)]

            async def execute(
                self, context: ActionContextSingle, result_builder: ResultBuilder
            ) -> Coroutine[Any, Any, Union[ActionResult, None]]:
                return result_builder.error('<div><p class="c-clr-1-4 l-mb">you failed</p></div>', {"type": "html"})

        self.product_collection.add_action("action_test", TestAction())

        result = self.loop.run_until_complete(self.product_collection.execute(self.mocked_caller, "action_test", {}))
        assert result == {
            "type": "Error",
            "message": '<div><p class="c-clr-1-4 l-mb">you failed</p></div>',
            "format": "html",
        }

    def test_execute_can_also_exec_synchronous_function(self):
        class TestAction(ActionSingle):
            SCOPE = ActionsScope.SINGLE
            FORM = [PlainNumberDynamicField(label="amount", type=ActionFieldType.NUMBER)]

            def execute(
                self, context: ActionContextSingle, result_builder: ResultBuilder
            ) -> Coroutine[Any, Any, Union[ActionResult, None]]:
                return None

        self.product_collection.add_action("action_test", TestAction())

        result = self.loop.run_until_complete(self.product_collection.execute(self.mocked_caller, "action_test", {}))
        assert result == {"type": "Success", "invalidated": set(), "format": "text", "message": "Success"}

    def test_should_throw_error_when_action_does_not_exists(self):
        self.assertRaisesRegex(
            ForestException,
            "🌳🌳🌳Action action_test is not implemented",
            self.loop.run_until_complete,
            self.product_collection.execute(self.mocked_caller, "action_test", {}),
        )

    def test_get_form_should_return_empty_array_when_action_not_exists(self):
        result = self.loop.run_until_complete(self.product_collection.get_form(self.mocked_caller, "action_test", {}))
        assert result == []

    def test_get_form_should_return_empty_array_when_action_form_is_empty(self):
        class TestAction(ActionSingle):
            SCOPE = ActionsScope.SINGLE

            async def execute(
                self, context: ActionContextSingle, result_builder: ResultBuilder
            ) -> Coroutine[Any, Any, Union[ActionResult, None]]:
                result_builder.success("Bravo !!!")

        self.product_collection.add_action("action_test", TestAction())
        result = self.loop.run_until_complete(self.product_collection.get_form(self.mocked_caller, "action_test", {}))
        assert result == []

    def test_get_form_should_return_array_of_action_field(self):
        self.product_collection.add_action("action_test", self.ActionSingle())

        result = self.loop.run_until_complete(self.product_collection.get_form(self.mocked_caller, "action_test", {}))

        assert result == [
            ActionField(
                label="amount",
                type=ActionFieldType.NUMBER,
                description="",
                is_read_only=False,
                is_required=False,
                value=None,
                collection_name=None,
                enum_values=None,
                watch_changes=False,
            )
        ]

    def test_get_form_should_compute_dynamic_default_values_on_load_hook(self):
        class TestAction(ActionSingle):
            SCOPE = ActionsScope.SINGLE
            FORM = [
                PlainStringDynamicField(
                    label="first_name", type=ActionFieldType.STRING, default_value=lambda context: "dynamic_default"
                ),
                PlainStringDynamicField(
                    label="last_name",
                    type=ActionFieldType.STRING,
                    is_read_only=lambda context: context.form_values.get("first_name") is not None,
                ),
            ]

            async def execute(
                self, context: ActionContextSingle, result_builder: ResultBuilder
            ) -> Coroutine[Any, Any, Union[ActionResult, None]]:
                result_builder.success("Bravo !!!")

        self.product_collection.add_action("action_test", TestAction())

        result = self.loop.run_until_complete(self.product_collection.get_form(self.mocked_caller, "action_test", {}))

        assert result == [
            ActionField(
                label="first_name",
                type=ActionFieldType.STRING,
                description="",
                is_read_only=False,
                is_required=False,
                value="dynamic_default",
                collection_name=None,
                enum_values=None,
                watch_changes=True,
            ),
            ActionField(
                label="last_name",
                type=ActionFieldType.STRING,
                description="",
                is_read_only=False,
                is_required=False,
                value=None,
                collection_name=None,
                enum_values=None,
                watch_changes=False,
            ),
        ]

    def test_get_form_should_compute_readonly_and_keep_null_firstname(self):
        class TestAction(ActionSingle):
            SCOPE = ActionsScope.SINGLE
            FORM = [
                PlainStringDynamicField(
                    label="first_name", type=ActionFieldType.STRING, default_value=lambda context: "dynamic_default"
                ),
                PlainStringDynamicField(
                    label="last_name",
                    type=ActionFieldType.STRING,
                    is_read_only=lambda context: context.form_values.get("first_name") is not None,
                ),
            ]

            async def execute(
                self, context: ActionContextSingle, result_builder: ResultBuilder
            ) -> Coroutine[Any, Any, Union[ActionResult, None]]:
                result_builder.success("Bravo !!!")

        self.product_collection.add_action("action_test", TestAction())

        result = self.loop.run_until_complete(
            self.product_collection.get_form(self.mocked_caller, "action_test", {"first_name": None})
        )

        assert result == [
            ActionField(
                label="first_name",
                type=ActionFieldType.STRING,
                description="",
                is_read_only=False,
                is_required=False,
                value=None,
                collection_name=None,
                enum_values=None,
                watch_changes=True,
            ),
            ActionField(
                label="last_name",
                type=ActionFieldType.STRING,
                description="",
                is_read_only=False,
                is_required=False,
                value=None,
                collection_name=None,
                enum_values=None,
                watch_changes=False,
            ),
        ]

    def test_get_form_should_compute_readonly_and_keep_firstname_value(self):
        class TestAction(ActionSingle):
            SCOPE = ActionsScope.SINGLE
            FORM = [
                PlainStringDynamicField(
                    label="first_name", type=ActionFieldType.STRING, default_value=lambda context: "dynamic_default"
                ),
                PlainStringDynamicField(
                    label="last_name",
                    type=ActionFieldType.STRING,
                    is_read_only=lambda context: context.form_values.get("first_name") is not None,
                ),
            ]

            async def execute(
                self, context: ActionContextSingle, result_builder: ResultBuilder
            ) -> Coroutine[Any, Any, Union[ActionResult, None]]:
                result_builder.success("Bravo !!!")

        self.product_collection.add_action("action_test", TestAction())

        result = self.loop.run_until_complete(
            self.product_collection.get_form(self.mocked_caller, "action_test", {"first_name": "John"})
        )

        assert result == [
            ActionField(
                label="first_name",
                type=ActionFieldType.STRING,
                description="",
                is_read_only=False,
                is_required=False,
                value="John",
                collection_name=None,
                enum_values=None,
                watch_changes=True,
            ),
            ActionField(
                label="last_name",
                type=ActionFieldType.STRING,
                description="",
                is_read_only=True,
                is_required=False,
                value=None,
                collection_name=None,
                enum_values=None,
                watch_changes=False,
            ),
        ]

    def test_get_form_should_compute_form_with_if_condition(self):
        class TestAction(ActionSingle):
            SCOPE = ActionsScope.SINGLE
            FORM = [
                PlainEnumDynamicField(label="rating", type=ActionFieldType.ENUM, enum_values=[1, 2, 3, 4, 5]),
                PlainStringDynamicField(
                    label="Put a comment",
                    type=ActionFieldType.STRING,
                    if_=lambda context: context.form_values.get("rating") is not None
                    and context.form_values["rating"] < 4,
                ),
            ]

            async def execute(
                self, context: ActionContextSingle, result_builder: ResultBuilder
            ) -> Coroutine[Any, Any, Union[ActionResult, None]]:
                result_builder.success("Bravo !!!")

        self.product_collection.add_action("action_test", TestAction())

        result = self.loop.run_until_complete(
            self.product_collection.get_form(self.mocked_caller, "action_test", {"first_name": "John"})
        )
        assert result == [
            ActionField(
                label="rating",
                type=ActionFieldType.ENUM,
                description="",
                is_read_only=False,
                is_required=False,
                value=None,
                collection_name=None,
                enum_values=[1, 2, 3, 4, 5],
                watch_changes=True,
            ),
        ]

    def test_get_form_should_work_with_changed_field(self):
        class TestAction(ActionSingle):
            SCOPE = ActionsScope.SINGLE
            FORM = [
                PlainEnumDynamicField(label="rating", type=ActionFieldType.ENUM, enum_values=[1, 2, 3, 4, 5]),
                PlainStringDynamicField(
                    label="Put a comment",
                    type=ActionFieldType.STRING,
                    if_=lambda context: context.changed_field == "rating",
                ),
            ]

            async def execute(
                self, context: ActionContextSingle, result_builder: ResultBuilder
            ) -> Coroutine[Any, Any, Union[ActionResult, None]]:
                result_builder.success("Bravo !!!")

        self.product_collection.add_action("action_test", TestAction())

        result = self.loop.run_until_complete(
            self.product_collection.get_form(self.mocked_caller, "action_test", {"first_name": "John"}, None, {})
        )
        assert result == [
            ActionField(
                label="rating",
                type=ActionFieldType.ENUM,
                description="",
                is_read_only=False,
                is_required=False,
                value=None,
                collection_name=None,
                enum_values=[1, 2, 3, 4, 5],
                watch_changes=False,
            ),
        ]
        result = self.loop.run_until_complete(
            self.product_collection.get_form(
                self.mocked_caller, "action_test", {"first_name": "John"}, None, {"changed_field": "rating"}
            )
        )
        assert result == [
            ActionField(
                label="rating",
                type=ActionFieldType.ENUM,
                description="",
                is_read_only=False,
                is_required=False,
                value=None,
                collection_name=None,
                enum_values=[1, 2, 3, 4, 5],
                watch_changes=False,
            ),
            ActionField(
                label="Put a comment",
                type=ActionFieldType.STRING,
                description="",
                is_read_only=False,
                is_required=False,
                value=None,
                collection_name=None,
                enum_values=None,
                watch_changes=False,
            ),
        ]

    def test_get_form_can_handle_multiple_form_of_fn(self):
        class TestAction(ActionSingle):
            @staticmethod
            def is_required(context):
                return True

            @staticmethod
            async def is_readonly(context):
                return True

            SCOPE = ActionsScope.SINGLE
            FORM = [
                PlainEnumDynamicField(
                    label="rating", type=ActionFieldType.ENUM, enum_values=[1, 2, 3, 4, 5], is_required=lambda ctx: True
                ),
                PlainStringDynamicField(
                    label="Put a comment",
                    type=ActionFieldType.STRING,
                    is_read_only=is_readonly,
                    is_required=is_required,
                    if_=lambda context: context.form_values.get("rating") is not None
                    and context.form_values["rating"] < 4,
                ),
            ]

            async def execute(
                self, context: ActionContextSingle, result_builder: ResultBuilder
            ) -> Coroutine[Any, Any, Union[ActionResult, None]]:
                result_builder.success("Bravo !!!")

        self.product_collection.add_action("action_test", TestAction())

        result = self.loop.run_until_complete(
            self.product_collection.get_form(self.mocked_caller, "action_test", {"rating": 2})
        )
        assert result == [
            ActionField(
                label="rating",
                type=ActionFieldType.ENUM,
                description="",
                is_read_only=False,
                is_required=True,
                value=2,
                collection_name=None,
                enum_values=[1, 2, 3, 4, 5],
                watch_changes=True,
            ),
            ActionField(
                label="Put a comment",
                type=ActionFieldType.STRING,
                description="",
                is_read_only=True,
                is_required=True,
                value=None,
                collection_name=None,
                enum_values=None,
                watch_changes=False,
            ),
        ]
