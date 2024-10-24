import asyncio
import logging
from unittest import TestCase
from unittest.mock import AsyncMock, Mock, patch

from forestadmin.agent_toolkit.agent import Agent
from forestadmin.agent_toolkit.exceptions import AgentToolkitException
from forestadmin.agent_toolkit.options import Options, OptionValidator
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.plugins.plugin import Plugin


@patch("forestadmin.agent_toolkit.agent.PermissionService")
@patch("forestadmin.agent_toolkit.agent.DatasourceCustomizer")
@patch("forestadmin.agent_toolkit.agent.Authentication")
@patch("forestadmin.agent_toolkit.agent.CapabilitiesResource")
@patch("forestadmin.agent_toolkit.agent.CrudResource")
@patch("forestadmin.agent_toolkit.agent.CrudRelatedResource")
@patch("forestadmin.agent_toolkit.agent.StatsResource")
@patch("forestadmin.agent_toolkit.agent.ActionResource")
@patch("forestadmin.agent_toolkit.agent.SchemaEmitter.get_serialized_schema", new_callable=AsyncMock)
@patch("forestadmin.agent_toolkit.agent.ForestHttpApi.send_schema", new_callable=AsyncMock)
class TestAgent(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()
        cls.fake_options: Options = Options(
            env_secret="da4fc9331a68a18c2262154c74d9acb22f335724c8f2a510f8df187fa808703e",
            auth_secret="fake_auth_secret",
            schema_path="./.forestadmin-schema.json",
        )

    def test_create(
        self,
        mocked_schema_emitter__get_serialized_schema,
        mocked_forest_http_api__send_schema,
        mocked_action_resource,
        mocked_stats_resource,
        mocked_crud_related_resource,
        mocked_crud_resource,
        mocked_capabilities_resource,
        mocked_authentication_resource,
        mocked_datasource_customizer,
        mocked_permission_service,
    ):
        with patch("forestadmin.agent_toolkit.agent.ForestLogger.setup_logger") as mock_logger:
            with patch(
                "forestadmin.agent_toolkit.agent.HttpResponseBuilder.setup_error_message_customizer"
            ) as mock_error_customizer:
                with patch(
                    "forestadmin.agent_toolkit.agent.OptionValidator.validate_options", side_effect=lambda x: x
                ) as mock_validate_option:
                    agent = Agent(self.fake_options)
                    mock_validate_option.assert_called_once()
                mock_logger.assert_called_with(logging.INFO, None)
                mock_error_customizer.assert_not_called()

        assert agent.options["prefix"] == OptionValidator.DEFAULT_OPTIONS["prefix"]
        assert agent.options["is_production"] == OptionValidator.DEFAULT_OPTIONS["is_production"]

        assert agent.options["server_url"] == OptionValidator.DEFAULT_OPTIONS["server_url"]
        assert agent.options["env_secret"] == self.fake_options["env_secret"]
        assert agent.options["auth_secret"] == self.fake_options["auth_secret"]

        assert agent.customizer is not None

        assert agent.META is None
        mocked_datasource_customizer.assert_called_once()
        mocked_permission_service.assert_called_once()

        def dumb_customize_error_function(error: Exception):
            return str(error)

        with patch(
            "forestadmin.agent_toolkit.agent.HttpResponseBuilder.setup_error_message_customizer"
        ) as mock_error_customizer:
            agent = Agent({**self.fake_options, "customize_error_message": dumb_customize_error_function})
            mock_error_customizer.assert_called_with(dumb_customize_error_function)

    def test_property_resources(
        self,
        mocked_schema_emitter__get_serialized_schema,
        mocked_forest_http_api__send_schema,
        mocked_action_resource,
        mocked_stats_resource,
        mocked_crud_related_resource,
        mocked_crud_resource,
        mocked_capabilities_resource,
        mocked_authentication_resource,
        mocked_datasource_customizer,
        mocked_permission_service,
    ):
        agent = Agent(self.fake_options)
        assert agent._resources is None
        with patch.object(agent.customizer, "get_datasource", new_callable=AsyncMock, return_value="fake_datasource"):
            resources = self.loop.run_until_complete(agent.get_resources())

            mocked_authentication_resource.assert_called_once_with(agent._ip_white_list_service, agent.options)
            mocked_capabilities_resource.assert_called_once_with(
                "fake_datasource", agent._ip_white_list_service, agent.options
            )
            mocked_crud_resource.assert_called_once_with(
                "fake_datasource", agent._permission_service, agent._ip_white_list_service, agent.options
            )
            mocked_crud_related_resource.assert_called_once_with(
                "fake_datasource", agent._permission_service, agent._ip_white_list_service, agent.options
            )
            mocked_stats_resource.assert_called_once_with(
                "fake_datasource", agent._permission_service, agent._ip_white_list_service, agent.options
            )
            mocked_action_resource.assert_called_once_with(
                "fake_datasource", agent._permission_service, agent._ip_white_list_service, agent.options
            )

        assert len(resources) == 8
        assert "capabilities" in resources
        assert "authentication" in resources
        assert "crud" in resources
        assert "crud_related" in resources
        assert "stats" in resources
        assert "actions" in resources
        assert "collection_charts" in resources
        assert "datasource_charts" in resources

    def test_property_meta(
        self,
        mocked_schema_emitter__get_serialized_schema,
        mocked_forest_http_api__send_schema,
        mocked_action_resource,
        mocked_stats_resource,
        mocked_crud_related_resource,
        mocked_crud_resource,
        mocked_capabilities_resource,
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
        mocked_capabilities_resource,
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
        mocked_capabilities_resource,
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

    def test_remove_collections(
        self,
        mocked_schema_emitter__get_serialized_schema,
        mocked_forest_http_api__send_schema,
        mocked_action_resource,
        mocked_stats_resource,
        mocked_crud_related_resource,
        mocked_crud_resource,
        mocked_capabilities_resource,
        mocked_authentication_resource,
        mocked_datasource_customizer,
        mocked_permission_service,
    ):
        agent = Agent(self.fake_options)

        with patch.object(agent.customizer, "remove_collections") as mock_remove_collections:
            agent.remove_collections("collection", "other_collection")

            mock_remove_collections.assert_called_with("collection", "other_collection")

    def test_customize_datasource(
        self,
        mocked_schema_emitter__get_serialized_schema,
        mocked_forest_http_api__send_schema,
        mocked_action_resource,
        mocked_stats_resource,
        mocked_crud_related_resource,
        mocked_crud_resource,
        mocked_capabilities_resource,
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
        mocked_capabilities_resource,
        mocked_authentication_resource,
        mocked_datasource_customizer,
        mocked_permission_service,
    ):
        agent = Agent({**self.fake_options, "logger_level": logging.DEBUG})
        agent.META = "fake_meta"

        agent.customizer.stack.datasource.collections = ["fake_collection"]

        with self.assertLogs("forestadmin", level=logging.DEBUG) as logger:
            with patch.object(
                agent.customizer,
                "get_datasource",
                new_callable=AsyncMock,
                return_value=agent.customizer.stack.datasource,
            ):
                self.loop.run_until_complete(agent._start())
            self.assertEqual(logger.output, ["DEBUG:forestadmin:Starting agent", "DEBUG:forestadmin:Agent started"])

        mocked_create_json_api_schema.assert_called_once_with("fake_collection")
        mocked_schema_emitter__get_serialized_schema.assert_called_once()
        mocked_forest_http_api__send_schema.assert_called_once()

        # test we can only launch start once
        mocked_create_json_api_schema.reset_mock()
        mocked_schema_emitter__get_serialized_schema.reset_mock()
        mocked_forest_http_api__send_schema.reset_mock()

        with self.assertLogs("forestadmin", level=logging.DEBUG) as logger:
            self.loop.run_until_complete(agent._start())
            self.assertEqual(logger.output, ["DEBUG:forestadmin:Agent already started."])

        mocked_create_json_api_schema.assert_not_called()
        mocked_schema_emitter__get_serialized_schema.assert_not_called()
        mocked_forest_http_api__send_schema.assert_not_called()

    def test_start_dont_crash_if_schema_generation_or_sending_fail(
        self,
        mocked_schema_emitter__get_serialized_schema,
        mocked_forest_http_api__send_schema,
        mocked_action_resource,
        mocked_stats_resource,
        mocked_crud_related_resource,
        mocked_crud_resource,
        mocked_capabilities_resource,
        mocked_authentication_resource,
        mocked_datasource_customizer,
        mocked_permission_service,
    ):
        agent = Agent({**self.fake_options, "logger_level": logging.DEBUG, "is_production": True})
        agent.META = "fake_meta"

        with patch(
            "forestadmin.agent_toolkit.agent.SchemaEmitter.get_serialized_schema",
            new_callable=AsyncMock,
            side_effect=Exception,
        ):
            with self.assertLogs("forestadmin", level=logging.DEBUG) as logger:
                Agent._Agent__IS_INITIALIZED = False
                with patch.object(agent.customizer, "get_datasource", new_callable=AsyncMock):
                    self.loop.run_until_complete(agent._start())

                self.assertEqual(logger.output[0], "DEBUG:forestadmin:Starting agent")
                self.assertTrue(logger.output[1].startswith("ERROR:forestadmin:Error generating forest schema"))
                self.assertEqual(
                    logger.output[2], "WARNING:forestadmin:Cannot send the apimap to Forest. Are you online?"
                )
                self.assertEqual(logger.output[3], "DEBUG:forestadmin:Agent started")
                self.assertEqual(len(logger.output), 4)

        mocked_forest_http_api__send_schema.assert_not_awaited()

    def test_use_should_add_a_plugin(
        self,
        mocked_schema_emitter__get_serialized_schema,
        mocked_forest_http_api__send_schema,
        mocked_action_resource,
        mocked_stats_resource,
        mocked_crud_related_resource,
        mocked_crud_resource,
        mocked_capabilities_resource,
        mocked_authentication_resource,
        mocked_datasource_customizer,
        mocked_permission_service,
    ):
        agent = Agent({**self.fake_options, "logger_level": logging.DEBUG, "is_production": True})

        class TestPlugin(Plugin):
            async def run(self, datasource_customizer, collection_customizer, options={}):
                pass

        with patch.object(agent.customizer, "use") as spy_use:
            agent.use(TestPlugin, {"my_option": 1})
            spy_use.assert_called_once_with(TestPlugin, {"my_option": 1})
