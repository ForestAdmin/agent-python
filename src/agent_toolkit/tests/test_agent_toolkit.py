import asyncio
import logging
import sys
from unittest import TestCase
from unittest.mock import Mock, patch

if sys.version_info < (3, 8):
    from mock import AsyncMock
else:
    from unittest.mock import AsyncMock

from forestadmin.agent_toolkit.agent import Agent
from forestadmin.agent_toolkit.exceptions import AgentToolkitException
from forestadmin.agent_toolkit.options import DEFAULT_OPTIONS, Options
from forestadmin.datasource_toolkit.datasources import Datasource


@patch("forestadmin.agent_toolkit.agent.PermissionService")
@patch("forestadmin.agent_toolkit.agent.DatasourceCustomizer")
@patch("forestadmin.agent_toolkit.agent.Authentication")
@patch("forestadmin.agent_toolkit.agent.CrudResource")
@patch("forestadmin.agent_toolkit.agent.CrudRelatedResource")
@patch("forestadmin.agent_toolkit.agent.StatsResource")
@patch("forestadmin.agent_toolkit.agent.ActionResource")
@patch("forestadmin.agent_toolkit.agent.SchemaEmitter.get_serialized_schema", new_callable=AsyncMock)
@patch("forestadmin.agent_toolkit.agent.ForestHttpApi.send_schema", new_callable=AsyncMock)
class TestAgent(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fake_options: Options = Options(
            env_secret="fake_env_secret",
            auth_secret="fake_auth_secret",
        )

    def test_create(
        self,
        mocked_schema_emitter__get_serialized_schema,
        mocked_forest_http_api__send_schema,
        mocked_action_resource,
        mocked_stats_resource,
        mocked_crud_related_resource,
        mocked_crud_resource,
        mocked_authentication_resource,
        mocked_datasource_customizer,
        mocked_permission_service,
    ):
        with patch("forestadmin.agent_toolkit.agent.ForestLogger.setup_logger") as mock_logger:
            agent = Agent(self.fake_options)
            mock_logger.assert_called_with(logging.WARNING, None)

        assert agent.options["prefix"] == DEFAULT_OPTIONS["prefix"]
        assert agent.options["is_production"] == DEFAULT_OPTIONS["is_production"]

        assert agent.options["forest_server_url"] == DEFAULT_OPTIONS["forest_server_url"]
        assert agent.options["env_secret"] == self.fake_options["env_secret"]
        assert agent.options["auth_secret"] == self.fake_options["auth_secret"]

        assert agent.customizer is not None

        assert agent.META is None
        mocked_datasource_customizer.assert_called_once()
        mocked_permission_service.assert_called_once()

    def test_property_resources(
        self,
        mocked_schema_emitter__get_serialized_schema,
        mocked_forest_http_api__send_schema,
        mocked_action_resource,
        mocked_stats_resource,
        mocked_crud_related_resource,
        mocked_crud_resource,
        mocked_authentication_resource,
        mocked_datasource_customizer,
        mocked_permission_service,
    ):
        agent = Agent(self.fake_options)
        assert agent._resources is None
        agent.resources

        mocked_authentication_resource.assert_called_once()
        mocked_crud_resource.assert_called_once()
        mocked_crud_related_resource.assert_called_once()
        mocked_stats_resource.assert_called_once()
        mocked_action_resource.assert_called_once()

        assert len(agent.resources) == 7
        assert "authentication" in agent.resources
        assert "crud" in agent.resources
        assert "crud_related" in agent.resources
        assert "stats" in agent.resources
        assert "actions" in agent.resources
        assert "collection_charts" in agent.resources
        assert "datasource_charts" in agent.resources

    def test_property_meta(
        self,
        mocked_schema_emitter__get_serialized_schema,
        mocked_forest_http_api__send_schema,
        mocked_action_resource,
        mocked_stats_resource,
        mocked_crud_related_resource,
        mocked_crud_resource,
        mocked_authentication_resource,
        mocked_datasource_customizer,
        mocked_permission_service,
    ):
        agent = Agent(self.fake_options)

        with self.assertRaises(AgentToolkitException):
            agent.meta

        agent.META = "fake_meta"
        assert agent.meta == "fake_meta"

    def test_add_datasource(
        self,
        mocked_schema_emitter__get_serialized_schema,
        mocked_forest_http_api__send_schema,
        mocked_action_resource,
        mocked_stats_resource,
        mocked_crud_related_resource,
        mocked_crud_resource,
        mocked_authentication_resource,
        mocked_datasource_customizer,
        mocked_permission_service,
    ):
        agent = Agent(self.fake_options)
        fake_datasource = Mock(Datasource)

        agent.add_datasource(fake_datasource)
        agent.customizer.add_datasource.assert_called_once_with(fake_datasource, {})
        assert agent._resources is None

    def test_add_chart(
        self,
        mocked_schema_emitter__get_serialized_schema,
        mocked_forest_http_api__send_schema,
        mocked_action_resource,
        mocked_stats_resource,
        mocked_crud_related_resource,
        mocked_crud_resource,
        mocked_authentication_resource,
        mocked_datasource_customizer,
        mocked_permission_service,
    ):
        agent = Agent(self.fake_options)

        def chart_fn(agent_context, result_builder):
            return result_builder.value(42)

        with patch.object(agent.customizer, "add_chart") as mock_add_chart:
            agent.add_chart("test_chart", chart_fn)

            mock_add_chart.assert_called_with("test_chart", chart_fn)

    def test_customize_datasource(
        self,
        mocked_schema_emitter__get_serialized_schema,
        mocked_forest_http_api__send_schema,
        mocked_action_resource,
        mocked_stats_resource,
        mocked_crud_related_resource,
        mocked_crud_resource,
        mocked_authentication_resource,
        mocked_datasource_customizer,
        mocked_permission_service,
    ):
        agent = Agent(self.fake_options)
        fake_datasource = Mock(Datasource)

        agent.add_datasource(fake_datasource)
        collection_name = "test"
        agent.customize_collection(collection_name)

        agent.customizer.customize_collection.assert_called_once_with(collection_name)

    @patch("forestadmin.agent_toolkit.agent.create_json_api_schema")
    def test_start(
        self,
        mocked_create_json_api_schema,
        mocked_schema_emitter__get_serialized_schema,
        mocked_forest_http_api__send_schema,
        mocked_action_resource,
        mocked_stats_resource,
        mocked_crud_related_resource,
        mocked_crud_resource,
        mocked_authentication_resource,
        mocked_datasource_customizer,
        mocked_permission_service,
    ):
        loop = asyncio.new_event_loop()

        agent = Agent({**self.fake_options, "logger_level": logging.DEBUG})
        agent.META = "fake_meta"

        agent.customizer.stack.datasource.collections = ["fake_collection"]

        with self.assertLogs("forestadmin", level=logging.DEBUG) as logger:
            loop.run_until_complete(agent.start())
            self.assertEqual(logger.output, ["DEBUG:forestadmin:Starting agent", "DEBUG:forestadmin:Agent started"])

        mocked_create_json_api_schema.assert_called_once_with("fake_collection")
        mocked_schema_emitter__get_serialized_schema.assert_called_once()
        mocked_forest_http_api__send_schema.assert_called_once()

        # test we can only launch start once
        mocked_create_json_api_schema.reset_mock()
        mocked_schema_emitter__get_serialized_schema.reset_mock()
        mocked_forest_http_api__send_schema.reset_mock()

        with self.assertLogs("forestadmin", level=logging.DEBUG) as logger:
            loop.run_until_complete(agent.start())
            self.assertEqual(logger.output, ["DEBUG:forestadmin:Agent already started."])

        mocked_create_json_api_schema.assert_not_called()
        mocked_schema_emitter__get_serialized_schema.assert_not_called()
        mocked_forest_http_api__send_schema.assert_not_called()

    @patch("forestadmin.agent_toolkit.agent.create_json_api_schema")
    def test_start_dont_crash_if_schema_generation_or_sending_fail(
        self,
        mocked_create_json_api_schema,
        mocked_schema_emitter__get_serialized_schema,
        mocked_forest_http_api__send_schema,
        mocked_action_resource,
        mocked_stats_resource,
        mocked_crud_related_resource,
        mocked_crud_resource,
        mocked_authentication_resource,
        mocked_datasource_customizer,
        mocked_permission_service,
    ):
        loop = asyncio.new_event_loop()

        agent = Agent({**self.fake_options, "logger_level": logging.DEBUG, "is_production": True})
        agent.META = "fake_meta"

        with patch(
            "forestadmin.agent_toolkit.agent.SchemaEmitter.get_serialized_schema",
            new_callable=AsyncMock,
            side_effect=Exception,
        ):
            with self.assertLogs("forestadmin", level=logging.DEBUG) as logger:
                loop.run_until_complete(agent.start())

                self.assertEqual(
                    logger.output,
                    [
                        "DEBUG:forestadmin:Starting agent",
                        "WARNING:forestadmin:Cannot send the apimap to Forest. Are you online?",
                        "DEBUG:forestadmin:Agent started",
                    ],
                )

        mocked_forest_http_api__send_schema.assert_not_awaited()
