import asyncio
import sys
from unittest import TestCase

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.action.context.base import ActionContext
from forestadmin.datasource_toolkit.decorators.action.fields import FormElementFactory, FormElementFactoryException
from forestadmin.datasource_toolkit.decorators.action.types.fields import (
    PlainCollectionDynamicField,
    PlainEnumDynamicField,
    PlainStringDynamicField,
)
from forestadmin.datasource_toolkit.interfaces.actions import ActionFieldType


class TestActionFieldFactory(TestCase):
    def test_field_factory_should_raise_if_unknown_type(self):
        plain_field = PlainStringDynamicField(
            type="bla",
            label="amount X10",
            description="test",
            is_required=True,
            is_read_only=True,
            if_=lambda ctx: "ok",
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
            if_=lambda ctx: "ok",
            value="1",
            default_value="10",
            error="err",
        )
        self.assertRaisesRegex(
            FormElementFactoryException,
            r"🌳🌳🌳Unable to build a field. cls: 'StringDynamicField', e: '(StringDynamicField\.)?__init__\(\) "
            "got an unexpected keyword argument 'error''",
            FormElementFactory.build,
            plain_field,
        )

    def test_field_factory_should_allow_widget_arguments(self):
        plain_field = PlainStringDynamicField(
            type=ActionFieldType.STRING,
            label="amount X10",
            description="test",
            is_required=True,
            is_read_only=True,
            if_=lambda ctx: "ok",
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


class BaseTestDynamicField(TestCase):
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
            value="1",
            default_value="10",
        )

        self.dynamic_field = FormElementFactory.build(self.plain_dynamic_field)

    def test_dynamic_field_should_also_return_collection_name(self):
        field = self.dynamic_field.dynamic_fields
        assert "Product" in field

    def test_to_action_field_should_set_collection_name(self):
        context = ActionContext(self.collection_product, self.mocked_caller, {}, {}, set())
        action_field = self.loop.run_until_complete(self.dynamic_field.to_action_field(context, "1"))

        assert action_field["collection_name"] == "Product"


class TestEnumDynamicField(BaseTestDynamicField):
    def setUp(self) -> None:
        self.plain_dynamic_field = PlainEnumDynamicField(
            type=ActionFieldType.ENUM,
            label="raiting",
            is_required=True,
            is_read_only=True,
            if_=lambda ctx: True,
            enum_values=[1, 2, 3, 4, 5],
        )

        self.dynamic_field = FormElementFactory.build(self.plain_dynamic_field)

    def test_dynamic_field_should_also_return_enum_values(self):
        field = self.dynamic_field.dynamic_fields
        assert [1, 2, 3, 4, 5] in field

    def test_to_action_field_should_set_collection_name(self):
        context = ActionContext(self.collection_product, self.mocked_caller, {}, {}, set())
        action_field = self.loop.run_until_complete(self.dynamic_field.to_action_field(context, "1"))

        assert action_field["enum_values"] == [1, 2, 3, 4, 5]


class TestEnumListDynamicField(BaseTestDynamicField):
    def setUp(self) -> None:
        self.plain_dynamic_field = PlainEnumDynamicField(
            type=ActionFieldType.ENUM_LIST,
            label="raiting",
            is_required=True,
            is_read_only=True,
            if_=lambda ctx: True,
            enum_values=[1, 2, 3, 4, 5],
        )

        self.dynamic_field = FormElementFactory.build(self.plain_dynamic_field)

    def test_dynamic_field_should_also_return_enum_values(self):
        field = self.dynamic_field.dynamic_fields
        assert [1, 2, 3, 4, 5] in field

    def test_to_action_field_should_set_collection_name(self):
        context = ActionContext(self.collection_product, self.mocked_caller, {}, {}, set())
        action_field = self.loop.run_until_complete(self.dynamic_field.to_action_field(context, ["1"]))

        assert action_field["enum_values"] == [1, 2, 3, 4, 5]


# BaseDynamicField
