from unittest import TestCase
from unittest.mock import Mock, call, patch

from forestadmin.flask_agent.agent import FlaskAgent, _after_request, create_agent


class TestFlaskAgent(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.options = {
            "env_secret": "da4fc9331a68a18c2262154c74d9acb22f335724c8f2a510f8df187fa808703e",
            "auth_secret": "fake",
        }
        cls.flask_app = Mock()
        cls.flask_app.config = {f"FOREST_{key.upper()}": value for key, value in cls.options.items()}
        cls.flask_app.config["FOREST_LOGGER"] = lambda level, message: print(level, message)
        cls.flask_app.config.update({"DEBUG": True})
        cls.flask_app.root_path = "/tmp"

        cls.flask_app.app_context.return_value.__enter__ = Mock(return_value=None)
        cls.flask_app.app_context.return_value.__exit__ = Mock(return_value=None)
        cls.flask_app.extensions = {}

    @patch("forestadmin.flask_agent.agent.asyncio.new_event_loop", return_value="event_loop")
    @patch("forestadmin.flask_agent.agent.build_blueprint", return_value="blueprint")
    def test_create_agent(self, mock_build_blueprint, mock_new_event_loop):
        agent = create_agent(self.flask_app)
        assert isinstance(agent, FlaskAgent)
        mock_new_event_loop.assert_called()
        mock_build_blueprint.assert_called()
        assert agent.blueprint == "blueprint"
        assert agent.loop == "event_loop"

        agent._blueprint = None
        self.assertRaises(Exception, getattr, agent, "blueprint")

    @patch("forestadmin.flask_agent.agent.build_blueprint", return_value="blueprint")
    def test_start(self, mock_build_blueprint):
        with patch.object(self.flask_app, "register_blueprint") as mocked_register_blueprint:
            agent = create_agent(self.flask_app)
            mocked_register_blueprint.assert_called_once_with("blueprint", url_prefix="/forest")
        agent.loop = Mock()

        with patch.object(agent, "_start", new_callable=Mock, return_value="started"):
            agent.start()
            agent.loop.run_until_complete.assert_called_once_with("started")

        assert agent.options["schema_path"] == "/tmp/.forestadmin-schema.json"

    @patch("forestadmin.flask_agent.agent.asyncio.get_event_loop", return_value="event_loop")
    @patch("forestadmin.flask_agent.agent.BaseAgent.get_resources")
    @patch("forestadmin.flask_agent.agent.Blueprint")
    def test_build_blueprint(self, mocked_blueprint, mock_base_agent_resources, mock_get_event_loop):
        agent = FlaskAgent(self.flask_app)
        mock_base_agent_resources.return_value = {
            "crud": Mock(),
            "crud_related": Mock(),
            "capabilities": Mock(),
            "authentication": Mock(),
            "stats": Mock(),
            "actions": Mock(),
            "collection_charts": Mock(),
            "datasource_charts": Mock(),
        }

        # blueprint = build_blueprint(agent) # called by __init__
        blueprint = agent.blueprint
        blueprint.after_request.assert_called_once_with(_after_request)
        calls = [
            call("", methods=["GET"]),
            call("/_internal/capabilities", methods=["POST"]),
            call("/authentication/callback", methods=["GET"]),
            call("/_actions/<collection_name>/<int:action_name>/<slug>/hooks/load", methods=["POST"]),
            call("/_actions/<collection_name>/<int:action_name>/<slug>/hooks/change", methods=["POST"]),
            call("/_actions/<collection_name>/<int:action_name>/<slug>/hooks/search", methods=["POST"]),
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

    def test_FlaskAgent_should_call_csrf_exempt_when_csrf_is_in_flask_extensions(self):
        csrf_extension_mock = Mock()
        csrf_extension_mock.exempt = Mock(side_effect=lambda view: view)
        with patch.dict(self.flask_app.extensions, {"csrf": csrf_extension_mock}):
            agent = FlaskAgent(self.flask_app)
            csrf_extension_mock.exempt.assert_called_once_with(agent._blueprint)
