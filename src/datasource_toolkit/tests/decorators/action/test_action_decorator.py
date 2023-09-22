import asyncio
import logging
import sys
from typing import Union
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
from forestadmin.datasource_toolkit.decorators.action.types.actions import ActionDict, ActionSingle
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
        async def execute(context: ActionContextSingle, result_builder: ResultBuilder) -> Union[ActionResult, None]:
            return result_builder.success("Bravo !!!")

        self.action_single: ActionDict = {
            "scope": ActionsScope.SINGLE,
            "execute": execute,
            "form": [{"type": ActionFieldType.NUMBER, "label": "amount"}],
        }

        self.datasource_decorator = DatasourceDecorator(self.datasource, ActionCollectionDecorator)
        self.product_collection = self.datasource_decorator.get_collection("Product")

    def test_add_action_should_add_action_in_actions_list(self):
        self.product_collection.add_action("action_test", self.action_single)

        assert "action_test" in self.product_collection.schema["actions"]

    def test_execute_should_return_success_response(self):
        self.product_collection.add_action("action_test", self.action_single)

        result = self.loop.run_until_complete(self.product_collection.execute(self.mocked_caller, "action_test", {}))

        assert result == {
            "type": "Success",
            "message": "Bravo !!!",
            "format": "text",
            "invalidated": set(),
        }

    def test_execute_return_default_response_when_result_is_not_result_builder_response(self):
        async def execute(context: ActionContextSingle, result_builder: ResultBuilder) -> Union[ActionResult, None]:
            return None

        test_action: ActionDict = {
            "scope": ActionsScope.SINGLE,
            "execute": execute,
            "form": [{"type": ActionFieldType.NUMBER, "label": "amount"}],
        }
        self.product_collection.add_action("action_test", test_action)

        result = self.loop.run_until_complete(self.product_collection.execute(self.mocked_caller, "action_test", {}))
        assert result == {"type": "Success", "invalidated": set(), "format": "text", "message": "Success"}

    def test_execute_return_correct_response_builder(self):
        async def execute(context: ActionContextSingle, result_builder: ResultBuilder) -> Union[ActionResult, None]:
            return result_builder.error('<div><p class="c-clr-1-4 l-mb">you failed</p></div>', {"type": "html"})

        test_action: ActionDict = {
            "scope": ActionsScope.SINGLE,
            "execute": execute,
            "form": [{"type": ActionFieldType.NUMBER, "label": "amount"}],
        }
        self.product_collection.add_action("action_test", test_action)

        result = self.loop.run_until_complete(self.product_collection.execute(self.mocked_caller, "action_test", {}))
        assert result == {
            "type": "Error",
            "message": '<div><p class="c-clr-1-4 l-mb">you failed</p></div>',
            "format": "html",
        }

    def test_execute_can_also_exec_synchronous_function(self):
        def execute(context: ActionContextSingle, result_builder: ResultBuilder) -> Union[ActionResult, None]:
            return None

        test_action: ActionDict = {
            "scope": ActionsScope.SINGLE,
            "execute": execute,
            "form": [{"type": ActionFieldType.NUMBER, "label": "amount"}],
        }
        self.product_collection.add_action("action_test", test_action)

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
        async def execute(context: ActionContextSingle, result_builder: ResultBuilder) -> Union[ActionResult, None]:
            result_builder.success("Bravo !!!")

        test_action: ActionDict = {
            "scope": ActionsScope.SINGLE,
            "execute": execute,
        }
        self.product_collection.add_action("action_test", test_action)

        result = self.loop.run_until_complete(self.product_collection.get_form(self.mocked_caller, "action_test", {}))
        assert result == []

    def test_get_form_should_return_array_of_action_field(self):
        self.product_collection.add_action("action_test", self.action_single)

        result = self.loop.run_until_complete(self.product_collection.get_form(self.mocked_caller, "action_test", {}))

        assert result == [
            ActionField(
                label="amount",
                type=ActionFieldType.NUMBER,
                description="",
                is_read_only=False,
                is_required=False,
                value=None,
                default_value=None,
                collection_name=None,
                enum_values=None,
                watch_changes=False,
            )
        ]

    def test_get_form_should_compute_dynamic_default_values_on_load_hook(self):
        async def execute(context: ActionContextSingle, result_builder: ResultBuilder) -> Union[ActionResult, None]:
            result_builder.success("Bravo !!!")

        test_action: ActionDict = {
            "scope": ActionsScope.SINGLE,
            "execute": execute,
            "form": [
                {
                    "label": "first_name",
                    "type": ActionFieldType.STRING,
                    "default_value": lambda context: "dynamic_default",
                },
                {
                    "label": "last_name",
                    "type": ActionFieldType.STRING,
                    "is_read_only": lambda context: context.form_values.get("first_name") is not None,
                },
            ],
        }
        self.product_collection.add_action("action_test", test_action)

        result = self.loop.run_until_complete(self.product_collection.get_form(self.mocked_caller, "action_test", {}))

        assert result == [
            {
                "label": "first_name",
                "type": ActionFieldType.STRING,
                "description": "",
                "is_read_only": False,
                "is_required": False,
                "value": "dynamic_default",
                "default_value": "dynamic_default",
                "collection_name": None,
                "enum_values": None,
                "watch_changes": True,
            },
            {
                "label": "last_name",
                "type": ActionFieldType.STRING,
                "description": "",
                "is_read_only": False,
                "is_required": False,
                "value": None,
                "collection_name": None,
                "enum_values": None,
                "default_value": None,
                "watch_changes": False,
            },
        ]

    def test_get_form_should_compute_readonly_and_keep_null_firstname(self):
        async def execute(context: ActionContextSingle, result_builder: ResultBuilder) -> Union[ActionResult, None]:
            result_builder.success("Bravo !!!")

        test_action: ActionDict = {
            "scope": ActionsScope.SINGLE,
            "execute": execute,
            "form": [
                {
                    "label": "first_name",
                    "type": ActionFieldType.STRING,
                    "default_value": lambda context: "dynamic_default",
                },
                {
                    "label": "last_name",
                    "type": ActionFieldType.STRING,
                    "is_read_only": lambda context: context.form_values.get("first_name") is not None,
                },
            ],
        }
        self.product_collection.add_action("action_test", test_action)

        result = self.loop.run_until_complete(
            self.product_collection.get_form(self.mocked_caller, "action_test", {"first_name": None})
        )

        assert result == [
            {
                "label": "first_name",
                "type": ActionFieldType.STRING,
                "description": "",
                "is_read_only": False,
                "is_required": False,
                "value": None,
                "default_value": "dynamic_default",
                "collection_name": None,
                "enum_values": None,
                "watch_changes": True,
            },
            {
                "label": "last_name",
                "type": ActionFieldType.STRING,
                "description": "",
                "is_read_only": False,
                "is_required": False,
                "value": None,
                "default_value": None,
                "collection_name": None,
                "enum_values": None,
                "watch_changes": False,
            },
        ]

    def test_get_form_should_compute_readonly_and_keep_firstname_value(self):
        async def execute(context: ActionContextSingle, result_builder: ResultBuilder) -> Union[ActionResult, None]:
            result_builder.success("Bravo !!!")

        test_action: ActionDict = {
            "scope": ActionsScope.SINGLE,
            "execute": execute,
            "form": [
                {
                    "label": "first_name",
                    "type": ActionFieldType.STRING,
                    "default_value": lambda context: "dynamic_default",
                },
                {
                    "label": "last_name",
                    "type": ActionFieldType.STRING,
                    "is_read_only": lambda context: context.form_values.get("first_name") is not None,
                },
            ],
        }
        self.product_collection.add_action("action_test", test_action)

        result = self.loop.run_until_complete(
            self.product_collection.get_form(self.mocked_caller, "action_test", {"first_name": "John"})
        )

        assert result == [
            {
                "label": "first_name",
                "type": ActionFieldType.STRING,
                "description": "",
                "is_read_only": False,
                "is_required": False,
                "value": "John",
                "default_value": "dynamic_default",
                "collection_name": None,
                "enum_values": None,
                "watch_changes": True,
            },
            {
                "label": "last_name",
                "type": ActionFieldType.STRING,
                "description": "",
                "is_read_only": True,
                "is_required": False,
                "value": None,
                "default_value": None,
                "collection_name": None,
                "enum_values": None,
                "watch_changes": False,
            },
        ]

    def test_get_form_should_compute_form_with_if_condition(self):
        async def execute(context: ActionContextSingle, result_builder: ResultBuilder) -> Union[ActionResult, None]:
            result_builder.success("Bravo !!!")

        test_action: ActionDict = {
            "scope": ActionsScope.SINGLE,
            "execute": execute,
            "form": [
                {
                    "label": "rating",
                    "type": ActionFieldType.ENUM,
                    "enum_values": [1, 2, 3, 4, 5],
                },
                {
                    "label": "Put a comment",
                    "type": ActionFieldType.STRING,
                    "if_": lambda context: context.form_values.get("rating") is not None
                    and context.form_values["rating"] < 4,
                },
            ],
        }
        self.product_collection.add_action("action_test", test_action)

        result = self.loop.run_until_complete(
            self.product_collection.get_form(self.mocked_caller, "action_test", {"first_name": "John"})
        )
        assert result == [
            {
                "label": "rating",
                "type": ActionFieldType.ENUM,
                "description": "",
                "is_read_only": False,
                "is_required": False,
                "value": None,
                "default_value": None,
                "collection_name": None,
                "enum_values": [1, 2, 3, 4, 5],
                "watch_changes": True,
            },
        ]

    def test_get_form_should_work_with_changed_field_warning(self):
        async def execute(context: ActionContextSingle, result_builder: ResultBuilder) -> Union[ActionResult, None]:
            result_builder.success("Bravo !!!")

        test_action: ActionDict = {
            "scope": ActionsScope.SINGLE,
            "execute": execute,
            "form": [
                {
                    "label": "rating",
                    "type": ActionFieldType.ENUM,
                    "enum_values": [1, 2, 3, 4, 5],
                },
                {
                    "label": "Put a comment",
                    "type": ActionFieldType.STRING,
                    "if_": lambda context: context.changed_field == "rating",
                },
            ],
        }

        self.product_collection.add_action("action_test", test_action)

        with self.assertLogs("forestadmin", level=logging.DEBUG) as logger:
            result = self.loop.run_until_complete(
                self.product_collection.get_form(self.mocked_caller, "action_test", {"first_name": "John"}, None, {})
            )
            self.assertEqual(
                logger.output,
                [
                    "WARNING:forestadmin:context.changed_field == 'field_name' is now deprecated, "
                    + "use context.has_field_changed('field_name') instead.",
                ],
            )
        assert result == [
            {
                "label": "rating",
                "type": ActionFieldType.ENUM,
                "description": "",
                "is_read_only": False,
                "is_required": False,
                "value": None,
                "default_value": None,
                "collection_name": None,
                "enum_values": [1, 2, 3, 4, 5],
                "watch_changes": False,
            },
        ]
        result = self.loop.run_until_complete(
            self.product_collection.get_form(
                self.mocked_caller, "action_test", {"first_name": "John"}, None, {"changed_field": "rating"}
            )
        )
        assert result == [
            {
                "label": "rating",
                "type": ActionFieldType.ENUM,
                "description": "",
                "is_read_only": False,
                "is_required": False,
                "value": None,
                "default_value": None,
                "collection_name": None,
                "enum_values": [1, 2, 3, 4, 5],
                "watch_changes": False,
            },
            {
                "label": "Put a comment",
                "type": ActionFieldType.STRING,
                "description": "",
                "is_read_only": False,
                "is_required": False,
                "value": None,
                "default_value": None,
                "collection_name": None,
                "enum_values": None,
                "watch_changes": False,
            },
        ]

    def test_get_form_should_make_dynamic_field_on_context_has_changed_field(self):
        async def execute(context: ActionContextSingle, result_builder: ResultBuilder) -> Union[ActionResult, None]:
            result_builder.success("Bravo !!!")

        test_action: ActionDict = {
            "scope": ActionsScope.SINGLE,
            "execute": execute,
            "form": [
                {
                    "label": "rating",
                    "type": ActionFieldType.ENUM,
                    "enum_values": [1, 2, 3, 4, 5],
                },
                {
                    "label": "Put a comment",
                    "type": ActionFieldType.STRING,
                    "if_": lambda context: context.has_field_changed("rating"),
                },
            ],
        }

        self.product_collection.add_action("action_test", test_action)

        result = self.loop.run_until_complete(
            self.product_collection.get_form(self.mocked_caller, "action_test", {"first_name": "John"}, None, {})
        )
        assert result == [
            {
                "label": "rating",
                "type": ActionFieldType.ENUM,
                "description": "",
                "is_read_only": False,
                "is_required": False,
                "value": None,
                "default_value": None,
                "collection_name": None,
                "enum_values": [1, 2, 3, 4, 5],
                "watch_changes": True,
            },
        ]
        result = self.loop.run_until_complete(
            self.product_collection.get_form(
                self.mocked_caller, "action_test", {"first_name": "John"}, None, {"changed_field": "rating"}
            )
        )
        assert result == [
            {
                "label": "rating",
                "type": ActionFieldType.ENUM,
                "description": "",
                "is_read_only": False,
                "is_required": False,
                "value": None,
                "default_value": None,
                "collection_name": None,
                "enum_values": [1, 2, 3, 4, 5],
                "watch_changes": True,
            },
            {
                "label": "Put a comment",
                "type": ActionFieldType.STRING,
                "description": "",
                "is_read_only": False,
                "is_required": False,
                "value": None,
                "default_value": None,
                "collection_name": None,
                "enum_values": None,
                "watch_changes": False,
            },
        ]

    def test_get_form_can_handle_multiple_form_of_fn(self):
        def is_required(context):
            return True

        async def is_readonly(context):
            return True

        async def execute(context: ActionContextSingle, result_builder: ResultBuilder) -> Union[ActionResult, None]:
            result_builder.success("Bravo !!!")

        test_action: ActionDict = {
            "scope": ActionsScope.SINGLE,
            "execute": execute,
            "form": [
                {
                    "label": "rating",
                    "type": ActionFieldType.ENUM,
                    "enum_values": [1, 2, 3, 4, 5],
                    "is_required": lambda ctx: True,
                },
                {
                    "label": "Put a comment",
                    "type": ActionFieldType.STRING,
                    "is_read_only": is_readonly,
                    "is_required": is_required,
                    "if_": lambda context: context.form_values.get("rating") is not None
                    and context.form_values["rating"] < 4,
                },
            ],
        }
        self.product_collection.add_action("action_test", test_action)

        result = self.loop.run_until_complete(
            self.product_collection.get_form(self.mocked_caller, "action_test", {"rating": 2})
        )
        assert result == [
            {
                "label": "rating",
                "type": ActionFieldType.ENUM,
                "description": "",
                "is_read_only": False,
                "is_required": True,
                "value": 2,
                "default_value": None,
                "collection_name": None,
                "enum_values": [1, 2, 3, 4, 5],
                "watch_changes": True,
            },
            {
                "label": "Put a comment",
                "type": ActionFieldType.STRING,
                "description": "",
                "is_read_only": True,
                "is_required": True,
                "value": None,
                "default_value": None,
                "collection_name": None,
                "enum_values": None,
                "watch_changes": False,
            },
        ]

    def test_action_decorator_works_with_old_style_actions(self):
        # TODO: remove this one when removing deprecation
        class ActionTest(ActionSingle):
            FORM = [
                {"type": ActionFieldType.NUMBER, "label": "value"},
                {
                    "type": ActionFieldType.NUMBER,
                    "label": "decimal",
                    "if_": lambda ctx: ctx.form_values.get("value") is not None,
                },
            ]

            def execute(self, context: ActionContextSingle, result_builder: ResultBuilder) -> Union[ActionResult, None]:
                return result_builder.success("cool")

        with self.assertLogs("forestadmin", level=logging.DEBUG) as logger:
            self.product_collection.add_action("action_test", ActionTest())
            self.assertEqual(
                logger.output,
                [
                    "WARNING:forestadmin:<class "
                    + "'test_action_decorator.TestActionCollectionCustomizer."
                    + "test_action_decorator_works_with_old_style_actions.<locals>.ActionTest'> Using action class is"
                    + " deprecated (ActionSingle, ActionBulk or ActionGlobal). Please use the dict syntax instead "
                    + "(doc: https://docs.forestadmin.com/developer-guide-agents-python/agent-customization/actions).",
                ],
            )

        result = self.loop.run_until_complete(self.product_collection.get_form(self.mocked_caller, "action_test", {}))
        assert result == [
            {
                "type": ActionFieldType.NUMBER,
                "label": "value",
                "description": "",
                "is_read_only": False,
                "is_required": False,
                "value": None,
                "default_value": None,
                "collection_name": None,
                "watch_changes": True,
                "enum_values": None,
            },
        ]
        result = self.loop.run_until_complete(
            self.product_collection.get_form(self.mocked_caller, "action_test", {"value": 10})
        )
        assert result == [
            {
                "label": "value",
                "type": ActionFieldType.NUMBER,
                "description": "",
                "is_read_only": False,
                "is_required": False,
                "value": 10,
                "default_value": None,
                "collection_name": None,
                "enum_values": None,
                "watch_changes": True,
            },
            {
                "label": "decimal",
                "type": ActionFieldType.NUMBER,
                "description": "",
                "is_read_only": False,
                "is_required": False,
                "value": None,
                "default_value": None,
                "collection_name": None,
                "enum_values": None,
                "watch_changes": False,
            },
        ]

        result = self.loop.run_until_complete(self.product_collection.execute(self.mocked_caller, "action_test", {}))
        assert result == {"type": "Success", "invalidated": set(), "format": "text", "message": "cool"}
