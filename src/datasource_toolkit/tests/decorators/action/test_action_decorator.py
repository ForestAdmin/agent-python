import asyncio
import sys
from typing import Union
from unittest import TestCase
from unittest.mock import ANY, Mock, patch

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
from forestadmin.datasource_toolkit.decorators.action.types.actions import ActionDict
from forestadmin.datasource_toolkit.decorators.datasource_decorator import DatasourceDecorator
from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException, ForestException
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

    def test_add_action_should_raise_if_multiple_field_with_same_id_are_provided(self):
        self.assertRaisesRegex(
            DatasourceToolkitException,
            r"All field must have different 'id'. Conflict come from field 'id'",
            self.product_collection.add_action,
            "action_test",
            {
                "scope": ActionsScope.SINGLE,
                "execute": lambda ctx, result_builder: result_builder.success(),
                "form": [
                    {
                        "type": ActionFieldType.LAYOUT,
                        "component": "Page",
                        "elements": [
                            {"type": ActionFieldType.NUMBER, "label": "cost", "id": "id"},
                            {
                                "type": ActionFieldType.LAYOUT,
                                "component": "Row",
                                "fields": [
                                    {"type": ActionFieldType.NUMBER, "label": "amount", "id": "id"},
                                ],
                            },
                        ],
                    }
                ],
            },
        )

    def test_add_action_should_raise_if_pages_and_others_are_mixed_at_root(self):
        self.assertRaisesRegex(
            DatasourceToolkitException,
            r"You cannot mix pages and other form elements in smart action 'action_test' form",
            self.product_collection.add_action,
            "action_test",
            {
                "scope": ActionsScope.SINGLE,
                "execute": lambda ctx, result_builder: result_builder.success(),
                "form": [
                    {
                        "type": ActionFieldType.LAYOUT,
                        "component": "Page",
                        "elements": [
                            {
                                "type": ActionFieldType.NUMBER,
                                "label": "cost",
                            },
                        ],
                    },
                    {
                        "type": ActionFieldType.NUMBER,
                        "label": "amount",
                    },
                ],
            },
        )

    def test_add_action_should_raise_if_multiple_field_in_row_subfield_with_same_id_are_provided(self):
        with patch.object(
            self.product_collection,
            "_validate_id_uniqueness",
            side_effect=self.product_collection._validate_id_uniqueness,
        ) as spy_validator:
            self.assertRaisesRegex(
                DatasourceToolkitException,
                r"All field must have different 'id'. Conflict come from field 'id'",
                self.product_collection.add_action,
                "action_test",
                {
                    "scope": ActionsScope.SINGLE,
                    "execute": lambda ctx, result_builder: result_builder.success(),
                    "form": [
                        {
                            "type": "Layout",
                            "component": "Row",
                            "fields": [
                                {"type": ActionFieldType.NUMBER, "label": "amount", "id": "id"},
                                {"type": ActionFieldType.NUMBER, "label": "label", "id": "different_id"},
                            ],
                        },
                        {"type": ActionFieldType.NUMBER, "label": "cost", "id": "id"},
                    ],
                },
            )
            self.assertEqual(spy_validator.call_count, 2)

    def test_execute_should_return_success_response(self):
        self.product_collection.add_action("action_test", self.action_single)

        result = self.loop.run_until_complete(self.product_collection.execute(self.mocked_caller, "action_test", {}))

        assert result == {
            "type": "Success",
            "message": "Bravo !!!",
            "format": "text",
            "invalidated": set(),
            "response_headers": {},
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
            "response_headers": {},
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
                id="amount",
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
            return result_builder.success("Bravo !!!")

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
                "id": "first_name",
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
                "id": "last_name",
                "type": ActionFieldType.STRING,
                "description": "",
                "is_read_only": True,
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
                "id": "first_name",
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
                "id": "last_name",
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
                "id": "first_name",
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
                "id": "last_name",
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
                    "enum_values": ["1", "2", "3", "4", "5"],
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
                "id": "rating",
                "type": ActionFieldType.ENUM,
                "description": "",
                "is_read_only": False,
                "is_required": False,
                "value": None,
                "default_value": None,
                "collection_name": None,
                "enum_values": ["1", "2", "3", "4", "5"],
                "watch_changes": True,
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
                    "enum_values": ["1", "2", "3", "4", "5"],
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
                "id": "rating",
                "type": ActionFieldType.ENUM,
                "description": "",
                "is_read_only": False,
                "is_required": False,
                "value": None,
                "default_value": None,
                "collection_name": None,
                "enum_values": ["1", "2", "3", "4", "5"],
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
                "id": "rating",
                "type": ActionFieldType.ENUM,
                "description": "",
                "is_read_only": False,
                "is_required": False,
                "value": None,
                "default_value": None,
                "collection_name": None,
                "enum_values": ["1", "2", "3", "4", "5"],
                "watch_changes": True,
            },
            {
                "id": "Put a comment",
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

    def test_get_form_should_make_dynamic_field_into_layout_elements_on_context_has_changed_field(self):
        async def execute(context: ActionContextSingle, result_builder: ResultBuilder) -> Union[ActionResult, None]:
            result_builder.success("Bravo !!!")

        test_action: ActionDict = {
            "scope": ActionsScope.SINGLE,
            "execute": execute,
            "form": [
                {
                    "type": "Layout",
                    "component": "Row",
                    "fields": [
                        {
                            "label": "rating",
                            "type": ActionFieldType.ENUM,
                            "enum_values": ["1", "2", "3", "4", "5"],
                        },
                        {
                            "label": "Put a comment",
                            "type": ActionFieldType.STRING,
                            "if_": lambda context: context.has_field_changed("rating"),
                        },
                    ],
                }
            ],
        }

        self.product_collection.add_action("action_test", test_action)

        result = self.loop.run_until_complete(
            self.product_collection.get_form(self.mocked_caller, "action_test", {"first_name": "John"}, None, {})
        )
        self.assertEqual(
            result,
            [
                {
                    "type": ActionFieldType.LAYOUT,
                    "component": "Row",
                    "fields": [
                        {
                            "label": "rating",
                            "id": "rating",
                            "type": ActionFieldType.ENUM,
                            "description": "",
                            "is_read_only": False,
                            "is_required": False,
                            "value": None,
                            "default_value": None,
                            "collection_name": None,
                            "enum_values": ["1", "2", "3", "4", "5"],
                            "watch_changes": True,
                        }
                    ],
                },
            ],
        )
        result = self.loop.run_until_complete(
            self.product_collection.get_form(
                self.mocked_caller, "action_test", {"first_name": "John"}, None, {"changed_field": "rating"}
            )
        )
        self.assertEqual(
            result,
            [
                {
                    "type": ActionFieldType.LAYOUT,
                    "component": "Row",
                    "fields": [
                        {
                            "label": "rating",
                            "id": "rating",
                            "type": ActionFieldType.ENUM,
                            "description": "",
                            "is_read_only": False,
                            "is_required": False,
                            "value": None,
                            "default_value": None,
                            "collection_name": None,
                            "enum_values": ["1", "2", "3", "4", "5"],
                            "watch_changes": True,
                        },
                        {
                            "label": "Put a comment",
                            "id": "Put a comment",
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
                    ],
                }
            ],
        )

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
                "id": "rating",
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
                "id": "Put a comment",
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

    def test_get_form_should_return_only_one_field_on_search_hook(self):
        def _search_fn(context, search_value):
            return [{"label": "1", "value": 1}, {"label": "2", "value": 2}]

        search_fn = Mock(wraps=_search_fn)

        test_action: ActionDict = {
            "scope": ActionsScope.SINGLE,
            "execute": lambda ctx, rslt_builder: rslt_builder.success("ok"),
            "form": [
                {
                    "label": "Put a comment",
                    "type": ActionFieldType.NUMBER,
                    "is_read_only": True,
                    "is_required": False,
                    "widget": "Dropdown",
                    "search": "dynamic",
                    "options": search_fn,
                },
            ],
        }

        self.product_collection.add_action("action_test", test_action)
        result = self.loop.run_until_complete(
            self.product_collection.get_form(
                self.mocked_caller,
                "action_test",
                {"Put a comment": 2},
                None,
                {"search_values": {"Put a comment": "2"}, "search_field": "Put a comment"},
            )
        )
        search_fn.assert_called_once_with(ANY, "2")
        self.assertEqual(len(result), 1)
        self.assertEqual(
            result,
            [
                {
                    "type": ActionFieldType.NUMBER,
                    "label": "Put a comment",
                    "id": "Put a comment",
                    "description": "",
                    "is_read_only": True,
                    "is_required": False,
                    "value": 2,
                    "default_value": None,
                    "collection_name": None,
                    "enum_values": None,
                    "watch_changes": False,
                    "widget": "Dropdown",
                    "search": "dynamic",
                    "options": [{"label": "1", "value": 1}, {"label": "2", "value": 2}],
                }
            ],
        )
