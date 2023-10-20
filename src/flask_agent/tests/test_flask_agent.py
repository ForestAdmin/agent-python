from unittest import TestCase
from unittest.mock import Mock, call, patch

from forestadmin.flask_agent.agent import Agent, _after_request, build_blueprint, create_agent


class TestFlaskAgent(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.options = {"env_secret": "fake", "auth_secret": "fake", "agent_url": "fake", "prefix": ""}

    @patch("forestadmin.flask_agent.agent.asyncio.new_event_loop", return_value="event_loop")
    @patch("forestadmin.flask_agent.agent.BaseAgent.__init__")
    @patch("forestadmin.flask_agent.agent.build_blueprint", return_value="blueprint")
    def test_create_agent(self, mock_build_blueprint, mock_base_agent, mock_new_event_loop):
        agent = create_agent(self.options)
        assert isinstance(agent, Agent)
        assert mock_new_event_loop.called
        assert mock_base_agent.called
        assert mock_build_blueprint.called
        assert agent.blueprint == "blueprint"
        assert agent.loop == "event_loop"

        agent._blueprint = None
        self.assertRaises(Exception, getattr, agent, "blueprint")

    @patch("forestadmin.flask_agent.agent.BaseAgent.__init__")
    @patch("forestadmin.flask_agent.agent.build_blueprint", return_value="blueprint")
    def test_register_blueprint(self, mock_build_blueprint, mock_base_agent):
        app = Mock()
        app.root_path = "/tmp"
        app.register_blueprint = Mock()
        agent = create_agent(self.options)
        agent.options = self.options
        agent.blueprint = "fake_blueprint"
        agent.loop = Mock()
        agent.start = Mock()
        agent.register_blueprint(app)

        assert agent.options["schema_path"] == "/tmp/.forestadmin-schema.json"
        app.register_blueprint.assert_called_once_with("fake_blueprint", url_prefix="/forest")
        agent.loop.run_until_complete.assert_called_once()

    @patch("forestadmin.flask_agent.agent.asyncio.get_event_loop", return_value="event_loop")
    @patch("forestadmin.flask_agent.agent.BaseAgent.get_resources")
    @patch("forestadmin.flask_agent.agent.BaseAgent.__init__")
    @patch("forestadmin.flask_agent.agent.Blueprint")
    def test_build_blueprint(self, mocked_blueprint, mock_base_agent, mock_base_agent_resources, mock_get_event_loop):
        agent = Agent(self.options)
        agent.options = self.options
        mock_base_agent_resources.return_value = {
            "crud": Mock(),
            "crud_related": Mock(),
            "authentication": Mock(),
            "stats": Mock(),
            "actions": Mock(),
            "collection_charts": Mock(),
            "datasource_charts": Mock(),
        }

        blueprint = build_blueprint(agent)
        blueprint.after_request.assert_called_once_with(_after_request)
        calls = [
            call("", methods=["GET"]),
            call("/authentication/callback", methods=["GET"]),
            call("/_actions/<collection_name>/<int:action_name>/<slug>/hooks/load", methods=["POST"]),
            call("/_actions/<collection_name>/<int:action_name>/<slug>/hooks/change", methods=["POST"]),
            call("/_actions/<collection_name>/<int:action_name>/<slug>", methods=["POST"]),
            call("/authentication", methods=["POST"]),
            call("/stats/<collection_name>", methods=["POST"]),
            call("/_charts/<chart_name>", methods=["POST", "GET"]),
            call("/_charts/<collection_name>/<chart_name>", methods=["POST", "GET"]),
            call("/<collection_name>/count", methods=["GET"]),
            call("/<collection_name>/<pks>", methods=["GET", "PUT", "DELETE"]),
            call("/<collection_name>", methods=["GET", "POST", "DELETE"]),
            call("/<collection_name>/<pks>/relationships/<relation_name>", methods=["GET", "POST", "DELETE", "PUT"]),
            call("/<collection_name>/<pks>/relationships/<relation_name>/count", methods=["GET"]),
            call("/<collection_name>.csv", methods=["GET"]),
            call("/<collection_name>/<pks>/relationships/<relation_name>.csv", methods=["GET"]),
            call("/scope-cache-invalidation", methods=["POST"]),
        ]
        blueprint.route.assert_has_calls(calls, any_order=True)
        assert blueprint.route.call_count == len(calls)
