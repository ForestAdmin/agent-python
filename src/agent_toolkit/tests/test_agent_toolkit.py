import asyncio
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
        agent = Agent(self.fake_options)

        assert agent.options["prefix"] == DEFAULT_OPTIONS["prefix"]
        assert agent.options["is_production"] == DEFAULT_OPTIONS["is_production"]

        assert agent.options["forest_server_url"] == DEFAULT_OPTIONS["forest_server_url"]
        assert agent.options["env_secret"] == self.fake_options["env_secret"]
        assert agent.options["auth_secret"] == self.fake_options["auth_secret"]

        assert agent.customizer is not None

        assert agent.META is None
        mocked_datasource_customizer.assert_called_once()
        mocked_permission_service.assert_called_once()
        mocked_authentication_resource.assert_called_once()
        mocked_crud_resource.assert_called_once()
        mocked_crud_related_resource.assert_called_once()
        mocked_stats_resource.assert_called_once()
        mocked_action_resource.assert_called_once()

    def test_properties(
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

        assert len(agent.resources) == 5
        assert "authentication" in agent.resources
        assert "crud" in agent.resources
        assert "crud_related" in agent.resources
        assert "stats" in agent.resources
        assert "actions" in agent.resources

        with self.assertRaises(AgentToolkitException):
            agent.meta

        agent.META = "fake_meta"
        assert agent.meta == "fake_meta"

    def test_methods(
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
        agent.customizer.add_datasource.assert_called_once_with(fake_datasource)

        collection_name = "test"
        agent.customize_collection(collection_name)
        agent.customizer.customize_collection.assert_called_once_with(collection_name)

        agent.META = "fake_meta"
        loop = asyncio.new_event_loop()
        loop.run_until_complete(agent.start())
        mocked_schema_emitter__get_serialized_schema.assert_called_once()
        mocked_forest_http_api__send_schema.assert_called_once()
