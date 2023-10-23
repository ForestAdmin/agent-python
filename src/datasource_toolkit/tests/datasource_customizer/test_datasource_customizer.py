import asyncio
import sys
from typing import Dict
from unittest import TestCase
from unittest.mock import AsyncMock, patch

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasource_customizer.datasource_customizer import DatasourceCustomizer
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.exceptions import ForestException
from forestadmin.datasource_toolkit.interfaces.fields import Column, FieldType, Operator, PrimitiveType
from forestadmin.datasource_toolkit.plugins.plugin import Plugin


class BaseTestDatasourceCustomizer(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()
        cls.datasource: Datasource = Datasource()
        Collection.__abstractmethods__ = set()  # to instantiate abstract class
        cls.collection_person = Collection("Person", cls.datasource)
        cls.collection_person.add_fields(
            {
                "id": Column(column_type=PrimitiveType.NUMBER, is_primary_key=True, type=FieldType.COLUMN),
                "first_name": Column(column_type=PrimitiveType.STRING, type=FieldType.COLUMN),
                "last_name": Column(column_type=PrimitiveType.STRING, type=FieldType.COLUMN),
            }
        )

        cls.collection_category = Collection("Category", cls.datasource)
        cls.collection_category.add_fields(
            {
                "id": Column(column_type=PrimitiveType.NUMBER, is_primary_key=True, type=FieldType.COLUMN),
                "label": Column(
                    column_type=PrimitiveType.STRING,
                    filter_operators=[Operator.LONGER_THAN, Operator.PRESENT],
                    type=FieldType.COLUMN,
                ),
            }
        )

        cls.datasource.add_collection(cls.collection_category)
        cls.datasource.add_collection(cls.collection_person)

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
        self.datasource_customizer = DatasourceCustomizer()


class TestDatasourceCustomizerAddDatasource(BaseTestDatasourceCustomizer):
    def test_add_datasource_should_add_collections_of_datasource(self):
        self.datasource_customizer.add_datasource(self.datasource)

        self.assertEqual(
            self.loop.run_until_complete(self.datasource_customizer.get_datasource()).get_collection("Person").name,
            "Person",
        )
        self.assertEqual(
            self.loop.run_until_complete(self.datasource_customizer.get_datasource()).get_collection("Category").name,
            "Category",
        )

    def test_add_datasource_should_hide_collection(self):
        self.datasource_customizer.add_datasource(self.datasource, {"exclude": ["Category"]})

        self.assertEqual(len(self.loop.run_until_complete(self.datasource_customizer.get_datasource()).collections), 1)
        self.assertEqual(
            self.loop.run_until_complete(self.datasource_customizer.get_datasource()).get_collection("Person").name,
            "Person",
        )

    def test_add_datasource_exclude_should_throw_when_collection_is_unknown(self):
        self.datasource_customizer.add_datasource(self.datasource, {"exclude": ["Foo"]})
        self.assertRaisesRegex(
            ForestException,
            r"🌳🌳🌳Collection 'Foo' not found",
            self.loop.run_until_complete,
            self.datasource_customizer.stack.apply_queue_customization(),
        )

    def test_add_datasource_should_add_only_a_specific_collection(self):
        self.datasource_customizer.add_datasource(self.datasource, {"include": ["Category"]})

        self.assertEqual(len(self.loop.run_until_complete(self.datasource_customizer.get_datasource()).collections), 1)
        self.assertEqual(
            self.loop.run_until_complete(self.datasource_customizer.get_datasource()).get_collection("Category").name,
            "Category",
        )

    def test_add_datasource_include_should_throw_when_collection_is_unknown(self):
        self.datasource_customizer.add_datasource(self.datasource, {"include": ["Foo"]})
        self.assertRaisesRegex(
            ForestException,
            r"🌳🌳🌳Collection 'Foo' not found",
            self.loop.run_until_complete,
            self.datasource_customizer.stack.apply_queue_customization(),
        )

    def test_add_datasource_should_rename_collection_without_error(self):
        self.datasource_customizer.add_datasource(self.datasource, {"rename": {"Category": "MyCategory"}})

        self.assertEqual(
            set(
                [c.name for c in self.loop.run_until_complete(self.datasource_customizer.get_datasource()).collections]
            ),
            set(["Person", "MyCategory"]),
        )

    def test_add_datasource_rename_should_throw_when_collection_is_unknown(self):
        self.datasource_customizer.add_datasource(self.datasource, {"rename": {"Foo": "Bar"}})
        self.assertRaisesRegex(
            ForestException,
            r"🌳🌳🌳Collection 'Foo' not found",
            self.loop.run_until_complete,
            self.datasource_customizer.stack.apply_queue_customization(),
        )


class TestDatasourceCustomizerCustomizeCollection(BaseTestDatasourceCustomizer):
    def test_customize_collection_should_provide_collection_customizer(self):
        self.datasource_customizer.add_datasource(self.datasource)
        collection_customizer = self.datasource_customizer.customize_collection("Category")
        collection_customizer.replace_field_sorting("label", None)

        self.assertEqual(
            self.loop.run_until_complete(self.datasource_customizer.get_datasource()).get_collection("Person").name,
            "Person",
        )
        self.assertEqual(
            self.loop.run_until_complete(self.datasource_customizer.get_datasource()).get_collection("Category").name,
            "Category",
        )


class TestDatasourceCustomizerRemoveCollection(BaseTestDatasourceCustomizer):
    def setUp(self) -> None:
        super().setUp()
        self.datasource_customizer.add_datasource(self.datasource)

    def test_remove_collection_should_work(self):
        self.datasource_customizer.remove_collections("Category")
        self.assertNotIn(
            "Category",
            set([c.name for c in self.datasource_customizer.collections]),
        )


class TestDatasourceCustomizerAddChart(BaseTestDatasourceCustomizer):
    def setUp(self) -> None:
        super().setUp()
        self.datasource_customizer.add_datasource(self.datasource)

    def test_add_chart_should_add_a_chart(self):
        def chart_fn(context, result_builder):
            return result_builder.value(1)

        with patch.object(
            self.datasource_customizer, "add_chart", wraps=self.datasource_customizer.add_chart
        ) as mocked_add_chart:
            self.datasource_customizer.add_chart("test_chart", chart_fn)
            self.loop.run_until_complete(self.datasource_customizer.stack.apply_queue_customization())
            schema = self.datasource_customizer.schema
        mocked_add_chart.assert_called_once_with("test_chart", chart_fn)

        assert "test_chart" in schema["charts"]
        assert schema["charts"]["test_chart"] == chart_fn


class TestDatasourceCustomizerUse(BaseTestDatasourceCustomizer):
    def setUp(self) -> None:
        super().setUp()
        self.datasource_customizer.add_datasource(self.datasource)

    def test_use_should_add_a_plugin(self):
        class TestPlugin(Plugin):
            async def run(self, datasource_customizer, collection_customizer, options: Dict):
                pass

        with patch.object(TestPlugin, "run", new_callable=AsyncMock) as plugin_spy:
            self.datasource_customizer.use(TestPlugin, {"my_option": 1})
            self.loop.run_until_complete(self.datasource_customizer.stack.apply_queue_customization())
            plugin_spy.assert_awaited_once_with(self.datasource_customizer, None, {"my_option": 1})
