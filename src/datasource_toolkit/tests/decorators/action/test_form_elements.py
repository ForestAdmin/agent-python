import asyncio
import sys
from unittest import TestCase
from unittest.mock import Mock, patch

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.action.context.base import ActionContext
from forestadmin.datasource_toolkit.decorators.action.form_elements import (
    DynamicFormElementException,
    DynamicLayoutElements,
    FormElementFactory,
    FormElementFactoryException,
)
from forestadmin.datasource_toolkit.decorators.action.types.fields import (
    PlainCollectionDynamicField,
    PlainDynamicField,
    PlainDynamicLayout,
    PlainEnumDynamicField,
    PlainFileDynamicField,
    PlainFileListDynamicField,
    PlainLayoutDynamicLayoutElementHtmlBlock,
    PlainLayoutDynamicLayoutElementPage,
    PlainLayoutDynamicLayoutElementRow,
    PlainLayoutDynamicLayoutElementSeparator,
    PlainListEnumDynamicField,
    PlainStringDynamicField,
    PlainStringDynamicFieldColorWidget,
)
from forestadmin.datasource_toolkit.interfaces.actions import ActionFieldType, File


class TestActionFormElementFactory(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()

    def test_field_factory_should_raise_if_unknown_type(self):
        plain_field = PlainStringDynamicField(
            type="bla",  # type:ignore
            label="amount X10",
            description="test",
            is_required=True,
            is_read_only=True,
            if_=lambda ctx: True,
            value="1",
            default_value="10",
        )
        self.assertRaisesRegex(
            FormElementFactoryException,
            r"🌳🌳🌳Unknown field type: 'bla'",
            FormElementFactory.build,
            plain_field,
        )

    def test_field_factory_should_raise_if_bad_param(self):
        plain_field = PlainStringDynamicField(
            type=ActionFieldType.STRING,
            label="amount X10",
            description="test",
            is_required=True,
            is_read_only=True,
            if_=lambda ctx: True,
            value="1",
            default_value="10",
            error="err",  # type:ignore
        )
        self.assertRaisesRegex(
            FormElementFactoryException,
            r"🌳🌳🌳Unable to build a field. cls: 'StringDynamicField', e: '(StringDynamicField\.)?__init__\(\) "
            "got an unexpected keyword argument 'error''",
            FormElementFactory.build,
            plain_field,
        )

    def test_field_factory_should_allow_widget_arguments(self):
        plain_field = PlainStringDynamicFieldColorWidget(
            type=ActionFieldType.STRING,
            label="amount X10",
            description="test",
            is_required=True,
            is_read_only=True,
            if_=lambda ctx: True,
            value="1",
            default_value="10",
            widget="ColorPicker",
            placeholder="placeholder",
            enable_opacity=False,
            quick_palette=None,
        )
        self.assertEqual(plain_field["widget"], "ColorPicker")
        self.assertEqual(plain_field["placeholder"], "placeholder")
        self.assertEqual(plain_field["enable_opacity"], False)
        self.assertEqual(plain_field["quick_palette"], None)

    def test_factory_should_create_layout(self):
        plain_field: PlainDynamicLayout = {"type": "Layout", "component": "Separator"}
        field = FormElementFactory.build(plain_field)
        self.assertEqual(field._if_, None)
        self.assertEqual(field._component, "Separator")  # type:ignore

    def test_should_create_id_in_copy_of_label(self):
        plain_field: PlainDynamicField = {"type": "String", "label": "test"}
        field = FormElementFactory.build(plain_field)
        self.assertEqual(field.id, "test")

    def test_should_create_with_label_and_id(self):
        plain_field: PlainDynamicField = {"type": "String", "id": "test", "label": "this is a label"}
        field = FormElementFactory.build(plain_field)
        self.assertEqual(field.label, "this is a label")
        self.assertEqual(field.id, "test")

    def test_should_raise_if_none_of_id_and_label(self):
        plain_field: PlainDynamicField = {"type": "String"}
        self.assertRaisesRegex(
            FormElementFactoryException,
            r"missing 1 required positional argument: 'label'",
            FormElementFactory.build,
            plain_field,
        )


class BaseTestDynamicField(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()

        cls.datasource: Datasource = Datasource()
        Collection.__abstractmethods__ = set()  # to instantiate abstract class  # type:ignore

        cls.collection_product = Collection("Product", cls.datasource)  # type:ignore
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


class TestFileDynamicField(BaseTestDynamicField):
    def test_when_having_default_value_field_should_be_dynamic(self):
        plain_dynamic_field = PlainFileDynamicField(
            type=ActionFieldType.FILE,
            label="collection",
            default_value=File("text/plain", b"dsqdsq", "test.txt"),
        )
        dynamic_field = FormElementFactory.build(plain_dynamic_field)
        self.assertTrue(dynamic_field.is_dynamic)


class TestFileListDynamicField(BaseTestDynamicField):
    def test_when_having_default_value_field_should_be_dynamic(self):
        plain_dynamic_field = PlainFileListDynamicField(
            type=ActionFieldType.FILE_LIST,
            label="collection",
            default_value=[File("text/plain", b"dsqdsq", "test.txt")],
        )
        dynamic_field = FormElementFactory.build(plain_dynamic_field)
        self.assertTrue(dynamic_field.is_dynamic)


class TestCollectionDynamicField(BaseTestDynamicField):
    def setUp(self) -> None:
        async def is_read_only(context):
            return True

        self.plain_dynamic_field = PlainCollectionDynamicField(
            collection_name="Product",
            type=ActionFieldType.COLLECTION,
            label="collection",
            description="collection",
            is_required=True,
            is_read_only=is_read_only,
            if_=True,
            value=["1"],
            default_value=["10"],
        )

        self.dynamic_field = FormElementFactory.build(self.plain_dynamic_field)

    def test_dynamic_field_should_also_return_collection_name(self):
        field = self.dynamic_field.dynamic_fields
        assert "Product" in field

    def test_to_action_field_should_set_collection_name(self):
        context = ActionContext(self.collection_product, self.mocked_caller, {}, {}, set())  # type:ignore
        action_field = self.loop.run_until_complete(self.dynamic_field.to_action_field(context, "1"))  # type:ignore

        assert action_field["collection_name"] == "Product"  # type:ignore


class TestEnumDynamicField(BaseTestDynamicField):
    def setUp(self) -> None:
        self.plain_dynamic_field = PlainEnumDynamicField(
            type=ActionFieldType.ENUM,
            label="raiting",
            is_required=True,
            is_read_only=True,
            if_=lambda ctx: True,
            enum_values=["1", "2", "3", "4", "5"],
        )

        self.dynamic_field = FormElementFactory.build(self.plain_dynamic_field)

    def test_dynamic_field_should_also_return_enum_values(self):
        field = self.dynamic_field.dynamic_fields
        assert ["1", "2", "3", "4", "5"] in field

    def test_to_action_field_should_set_collection_name(self):
        context = ActionContext(self.collection_product, self.mocked_caller, {}, {}, set())  # type:ignore
        action_field = self.loop.run_until_complete(self.dynamic_field.to_action_field(context, "1"))  # type:ignore

        assert action_field["enum_values"] == ["1", "2", "3", "4", "5"]  # type:ignore


class TestEnumListDynamicField(BaseTestDynamicField):
    def setUp(self) -> None:
        self.plain_dynamic_field = PlainListEnumDynamicField(
            type=ActionFieldType.ENUM_LIST,
            label="raiting",
            is_required=True,
            is_read_only=True,
            if_=lambda ctx: True,
            enum_values=["1", "2", "3", "4", "5"],
        )

        self.dynamic_field = FormElementFactory.build(self.plain_dynamic_field)

    def test_dynamic_field_should_also_return_enum_values(self):
        field = self.dynamic_field.dynamic_fields
        assert ["1", "2", "3", "4", "5"] in field

    def test_to_action_field_should_set_collection_name(self):
        context = ActionContext(self.collection_product, self.mocked_caller, {}, {}, set())  # type:ignore
        action_field = self.loop.run_until_complete(self.dynamic_field.to_action_field(context, ["1"]))  # type:ignore

        assert action_field["enum_values"] == ["1", "2", "3", "4", "5"]  # type:ignore


class TestLayoutDynamicElementSeparator(BaseTestDynamicField):
    def setUp(self) -> None:
        self.plain_dynamic_layout = PlainLayoutDynamicLayoutElementSeparator(
            type="Layout", if_=lambda ctx: ctx.form_values.get("desired_value", False), component="Separator"
        )

        self.dynamic_field = FormElementFactory.build(self.plain_dynamic_layout)

    def test_should_always_been_dynamic(self):
        # TODO: this test must be remove at story#7
        field = FormElementFactory.build(PlainLayoutDynamicLayoutElementSeparator(type="Layout", component="Separator"))
        self.assertEqual(field.is_dynamic, True)

    def test_should_evaluate_if(self):
        ctx = Mock()
        ctx.form_values = {"desired_value": True}
        self.assertEqual(self.loop.run_until_complete(self.dynamic_field.if_(ctx)), True)
        ctx.form_values = {"desired_value": False}
        self.assertEqual(self.loop.run_until_complete(self.dynamic_field.if_(ctx)), False)

    def test_should_generate_action_field(self):
        ctx = Mock()
        ctx.form_values = {"desired_value": True}

        action_field = self.loop.run_until_complete(self.dynamic_field.to_action_field(ctx, ctx.form_values))
        self.assertEqual(action_field, {"type": ActionFieldType.LAYOUT, "component": "Separator"})


class TestLayoutDynamicElementHtmlBlock(BaseTestDynamicField):
    def setUp(self) -> None:
        self.plain_dynamic_layout = PlainLayoutDynamicLayoutElementHtmlBlock(
            type="Layout", component="HtmlBlock", content=lambda ctx: f'<b>{ctx.form_values.get("desired_value")}</b>'
        )

        self.dynamic_field = FormElementFactory.build(self.plain_dynamic_layout)

    def test_should_generate_action_field_with_evaluation(self):
        ctx = Mock()
        ctx.form_values = {"desired_value": True}

        action_field = self.loop.run_until_complete(self.dynamic_field.to_action_field(ctx, ctx.form_values))
        self.assertEqual(
            action_field, {"type": ActionFieldType.LAYOUT, "component": "HtmlBlock", "content": "<b>True</b>"}
        )


class TestLayoutDynamicElementRow(BaseTestDynamicField):
    def test_should_generate_action_field(self):
        plain_field = PlainLayoutDynamicLayoutElementRow(
            type="Layout",
            component="Row",
            fields=[
                {"type": "String", "label": "gender"},
                {"type": "String", "label": "gender_other"},
            ],
        )
        ctx = Mock()
        ctx.form_values = {}
        dynamic_field = FormElementFactory.build(plain_field)

        action_field = self.loop.run_until_complete(dynamic_field.to_action_field(ctx, ctx.form_values))

        self.assertEqual(
            action_field,
            {
                "type": ActionFieldType.LAYOUT,
                "component": "Row",
                "fields": [
                    {
                        "type": ActionFieldType.STRING,
                        "id": "gender",
                        "label": "gender",
                        "description": "",
                        "is_read_only": False,
                        "is_required": False,
                        "value": None,
                        "default_value": None,
                        "collection_name": None,
                        "enum_values": None,
                        "watch_changes": False,
                    },
                    {
                        "type": ActionFieldType.STRING,
                        "label": "gender_other",
                        "id": "gender_other",
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
            },
        )

    def test_should_generate_action_field_with_evaluation(self):
        plain_field = PlainLayoutDynamicLayoutElementRow(
            type="Layout",
            component="Row",
            fields=[
                {"type": "String", "label": "gender"},
                {
                    "type": "String",
                    "label": "gender_other",
                    "if_": lambda ctx: ctx.form_values.get("gender", "") == "other",
                },
            ],
        )
        dynamic_field = FormElementFactory.build(plain_field)
        ctx = Mock()
        ctx.form_values = {"gender": "other"}
        action_field = self.loop.run_until_complete(dynamic_field.to_action_field(ctx, ctx.form_values))
        self.assertEqual(
            action_field,
            {
                "type": ActionFieldType.LAYOUT,
                "component": "Row",
                "fields": [
                    {
                        "type": ActionFieldType.STRING,
                        "label": "gender",
                        "id": "gender",
                        "description": "",
                        "is_read_only": False,
                        "is_required": False,
                        "value": "other",
                        "default_value": None,
                        "collection_name": None,
                        "enum_values": None,
                        "watch_changes": False,
                    },
                    {
                        "type": ActionFieldType.STRING,
                        "label": "gender_other",
                        "id": "gender_other",
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
            },
        )

    def test_should_recursively_call_form_element_builder(self):
        plain_field = PlainLayoutDynamicLayoutElementRow(
            type="Layout",
            component="Row",
            fields=[
                {"type": "String", "label": "gender"},
                {"type": "String", "label": "gender_other"},
            ],
        )
        with patch(
            "forestadmin.datasource_toolkit.decorators.action.form_elements.FormElementFactory.build",
            side_effect=FormElementFactory.build,
        ) as mock_build:
            FormElementFactory.build(plain_field)
            mock_build.assert_any_call(plain_field)
            mock_build.assert_any_call(plain_field["fields"][0])

    def test_should_not_be_generated_if_no_content(self):
        plain_field = PlainLayoutDynamicLayoutElementRow(
            type="Layout",
            component="Row",
            fields=[
                {"type": "String", "label": "gender", "if_": lambda ctx: ctx.form_values.get("ask_gender") is True},
                {
                    "type": "String",
                    "label": "gender_other",
                    "if_": lambda ctx: ctx.form_values.get("gender", "") == "other",
                },
            ],
        )
        dynamic_field = FormElementFactory.build(plain_field)
        ctx = Mock()
        ctx.form_values = {}
        action_field = self.loop.run_until_complete(dynamic_field.to_action_field(ctx, ctx.form_values))
        self.assertEqual(action_field, None)

    def test_should_raise_if_contains_layout(self):
        # with plain field
        plain_field = PlainLayoutDynamicLayoutElementRow(
            type="Layout",
            component="Row",
            fields=[
                {"type": "Layout", "component": "HtmlBlock", "content": "bla"},  # type: ignore
                {
                    "type": "String",
                    "label": "gender_other",
                    "if_": lambda ctx: ctx.form_values.get("gender", "") == "other",
                },
            ],
        )
        self.assertRaisesRegex(
            DynamicFormElementException,
            r"A 'Row' form element doesn't allow layout elements as subfields.",
            FormElementFactory.build,
            plain_field,
        )
        # with dynamic field
        plain_field = PlainLayoutDynamicLayoutElementRow(
            type="Layout",
            component="Row",
            fields=[
                DynamicLayoutElements("HtmlBlock", None, content="bla"),  # type: ignore
                {
                    "type": "String",
                    "label": "gender_other",
                    "if_": lambda ctx: ctx.form_values.get("gender", "") == "other",
                },
            ],
        )
        self.assertRaisesRegex(
            DynamicFormElementException,
            r"A 'Row' form element doesn't allow layout elements as subfields.",
            FormElementFactory.build,
            plain_field,
        )

    def test_should_raise_if_no_fields_present(self):
        plain_field = PlainLayoutDynamicLayoutElementRow(
            type="Layout",
            component="Row",
        )  # type:ignore
        self.assertRaisesRegex(
            DynamicFormElementException,
            r"Using 'fields' in a 'Row' configuration is mandatory.",
            FormElementFactory.build,
            plain_field,
        )


class TestLayoutDynamicElementPage(BaseTestDynamicField):
    def test_should_generate_action_field(self):
        plain_field = PlainLayoutDynamicLayoutElementPage(
            type="Layout",
            component="Page",
            elements=[
                {"type": "String", "label": "firstname"},
                {"type": "String", "label": "lastname"},
            ],
            next_button_label="next",
            previous_button_label="previous",
        )
        ctx = Mock()
        ctx.form_values = {}
        dynamic_field = FormElementFactory.build(plain_field)

        action_field = self.loop.run_until_complete(dynamic_field.to_action_field(ctx, ctx.form_values))

        self.assertEqual(
            action_field,
            {
                "type": ActionFieldType.LAYOUT,
                "component": "Page",
                "next_button_label": "next",
                "previous_button_label": "previous",
                "elements": [
                    {
                        "type": ActionFieldType.STRING,
                        "id": "firstname",
                        "label": "firstname",
                        "description": "",
                        "is_read_only": False,
                        "is_required": False,
                        "value": None,
                        "default_value": None,
                        "collection_name": None,
                        "enum_values": None,
                        "watch_changes": False,
                    },
                    {
                        "type": ActionFieldType.STRING,
                        "label": "lastname",
                        "id": "lastname",
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
            },
        )

    def test_should_generate_action_field_with_evaluation(self):
        plain_field = PlainLayoutDynamicLayoutElementPage(
            type="Layout",
            component="Page",
            if_=lambda ctx: True,
            elements=[
                {"type": "String", "label": "firstname"},
                {"type": "String", "label": "lastname"},
            ],
            next_button_label=lambda ctx: "next",
            previous_button_label=lambda ctx: "previous",
        )
        dynamic_field = FormElementFactory.build(plain_field)
        ctx = Mock()
        ctx.form_values = {}
        action_field = self.loop.run_until_complete(dynamic_field.to_action_field(ctx, ctx.form_values))
        self.assertEqual(
            action_field,
            {
                "type": ActionFieldType.LAYOUT,
                "component": "Page",
                "next_button_label": "next",
                "previous_button_label": "previous",
                "elements": [
                    {
                        "type": ActionFieldType.STRING,
                        "id": "firstname",
                        "label": "firstname",
                        "description": "",
                        "is_read_only": False,
                        "is_required": False,
                        "value": None,
                        "default_value": None,
                        "collection_name": None,
                        "enum_values": None,
                        "watch_changes": False,
                    },
                    {
                        "type": ActionFieldType.STRING,
                        "label": "lastname",
                        "id": "lastname",
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
            },
        )

    def test_should_recursively_call_form_element_builder(self):
        plain_field = PlainLayoutDynamicLayoutElementPage(
            type="Layout",
            component="Page",
            elements=[
                {"type": "String", "label": "firstname"},
                {"type": "String", "label": "lastname"},
            ],
        )
        with patch(
            "forestadmin.datasource_toolkit.decorators.action.form_elements.FormElementFactory.build",
            side_effect=FormElementFactory.build,
        ) as mock_build:
            FormElementFactory.build(plain_field)
            mock_build.assert_any_call(plain_field)
            mock_build.assert_any_call(plain_field["elements"][0])
            mock_build.assert_any_call(plain_field["elements"][1])

    def test_should_not_be_generated_if_no_content(self):
        plain_field = PlainLayoutDynamicLayoutElementPage(
            type="Layout",
            component="Page",
            elements=[
                {"type": "String", "label": "firstname", "if_": lambda ctx: False},
                {"type": "String", "label": "lastname", "if_": lambda ctx: False},
            ],
            next_button_label="next",
            previous_button_label="previous",
        )
        dynamic_field = FormElementFactory.build(plain_field)
        ctx = Mock()
        ctx.form_values = {}
        action_field = self.loop.run_until_complete(dynamic_field.to_action_field(ctx, ctx.form_values))
        self.assertEqual(action_field, None)

    def test_should_raise_if_contains_page(self):
        # with plain field
        plain_field = PlainLayoutDynamicLayoutElementPage(
            type="Layout",
            component="Page",
            elements=[
                {"type": "String", "label": "firstname", "if_": lambda ctx: False},
                {"type": "String", "label": "lastname", "if_": lambda ctx: False},
                {"type": "Layout", "component": "Page", "elements": []},
            ],
        )
        self.assertRaisesRegex(
            DynamicFormElementException,
            r"A 'Page' form element doesn't allow sub pages as elements.",
            FormElementFactory.build,
            plain_field,
        )
        # with dynamic field
        plain_field = PlainLayoutDynamicLayoutElementPage(
            type="Layout",
            component="Page",
            elements=[
                {"type": "String", "label": "firstname", "if_": lambda ctx: False},
                {"type": "String", "label": "lastname", "if_": lambda ctx: False},
                DynamicLayoutElements(component="Page", elements=[]),  # type: ignore
            ],
        )
        self.assertRaisesRegex(
            DynamicFormElementException,
            r"A 'Page' form element doesn't allow sub pages as elements.",
            FormElementFactory.build,
            plain_field,
        )

    def test_should_raise_if_no_elements_present(self):
        plain_field = PlainLayoutDynamicLayoutElementPage(
            type="Layout",
            component="Page",
        )  # type: ignore
        self.assertRaisesRegex(
            DynamicFormElementException,
            r"Using 'elements' in a 'Page' configuration is mandatory.",
            FormElementFactory.build,
            plain_field,
        )
