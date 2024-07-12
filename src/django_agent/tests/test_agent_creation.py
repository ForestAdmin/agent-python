import os
import threading
import time
from unittest import TestCase
from unittest.mock import ANY, AsyncMock, Mock, patch

from django.apps import apps
from django.test import TestCase as DjangoTestCase
from django.test import override_settings
from forestadmin.django_agent.agent import DjangoAgent, create_agent
from forestadmin.django_agent.apps import init_app_agent, is_launch_as_server


class TestDjangoAgentCreation(DjangoTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.dj_options = {
            "FOREST_ENV_SECRET": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
            "FOREST_AUTH_SECRET": "de1s5LAbFFAPRvCJQTLb",
            "FOREST_CUSTOMIZE_FUNCTION": lambda agent: None,
            "FOREST_LOGGER": lambda level, msg: None,
        }

    def test_init_should_parse_settings(self):
        with override_settings(**self.dj_options):
            agent: DjangoAgent = DjangoAgent()
            self.assertEqual(agent.options["auth_secret"], "de1s5LAbFFAPRvCJQTLb")
            self.assertEqual(
                agent.options["env_secret"], "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
            )
            self.assertEqual(
                agent.options["schema_path"],
                os.path.abspath(os.path.join(__file__, "..", "test_project_agent", ".forestadmin-schema.json")),
            )

    def test_init_should_compute_schema_path_with_and_without_base_dir_setting(self):
        with override_settings(
            **self.dj_options, **{"BASE_DIR": os.path.abspath(os.path.join(__file__, "..", "test_project_agent"))}
        ):
            agent: DjangoAgent = DjangoAgent()
            self.assertEqual(
                agent.options["schema_path"],
                os.path.abspath(os.path.join(__file__, "..", "test_project_agent", ".forestadmin-schema.json")),
            )

        with override_settings(**self.dj_options):
            agent: DjangoAgent = DjangoAgent()
            self.assertEqual(
                agent.options["schema_path"],
                os.path.abspath(os.path.join(__file__, "..", "test_project_agent", ".forestadmin-schema.json")),
            )

    def test_create_agent_should_create_agent_with_django_settings(self):
        with override_settings(**self.dj_options):
            agent: DjangoAgent = create_agent()

            self.assertEqual(agent.options["auth_secret"], "de1s5LAbFFAPRvCJQTLb")
            self.assertEqual(
                agent.options["env_secret"], "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
            )
            self.assertEqual(
                agent.options["schema_path"],
                os.path.abspath(os.path.join(__file__, "..", "test_project_agent", ".forestadmin-schema.json")),
            )

    def test_create_agent_should_create_agent_with_given_settings(self):
        agent: DjangoAgent = create_agent(
            {
                "auth_secret": "11111111111111111111",
                "env_secret": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
                "schema_path": "./.forestadmin-schema.json",
            }
        )

        self.assertEqual(agent.options["auth_secret"], "11111111111111111111")
        self.assertEqual(
            agent.options["env_secret"], "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
        )
        self.assertEqual(agent.options["schema_path"], "./.forestadmin-schema.json")

    def test_agent_start_should_call_base_agent_start(self):
        agent: DjangoAgent = create_agent()

        with patch.object(agent, "_start", new_callable=AsyncMock) as mock_base_start:
            agent.start()
            mock_base_start.assert_awaited_once()


class TestDjangoAgentLaunchAsServer(TestCase):
    def test_is_launch_as_server_should_return_False_on_pytest_and_other_no_runserver_manage_command(self):
        with patch("forestadmin.django_agent.apps.sys.argv", ["manage.py", "migrate"]):
            self.assertFalse(is_launch_as_server())

        with patch("forestadmin.django_agent.apps.sys.argv", ["pytest"]):
            self.assertFalse(is_launch_as_server())

        with patch("forestadmin.django_agent.apps.sys.argv", ["mypy"]):
            self.assertFalse(is_launch_as_server())

    def test_is_launch_as_server_should_return_True_on_no_pytest_and_other_runserver_manage_command(self):
        with patch("forestadmin.django_agent.apps.sys.argv", ["manage.py", "runserver"]):
            self.assertTrue(is_launch_as_server())

        with patch("forestadmin.django_agent.apps.sys.argv", []):
            self.assertTrue(is_launch_as_server())


class TestDjangoAgentInitAppAgent(DjangoTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.dj_options = {
            "FOREST_ENV_SECRET": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
            "FOREST_AUTH_SECRET": "de1s5LAbFFAPRvCJQTLb",
            "FOREST_CUSTOMIZE_FUNCTION": lambda agent: None,
            "FOREST_LOGGER": lambda level, msg: None,
        }

    def test_should_add_datasource_when_no_setting(self):
        with override_settings(**self.dj_options):
            with patch(
                "forestadmin.django_agent.apps.DjangoDatasource", return_value="dj_datasource"
            ) as mock_django_datasource:
                with patch.object(DjangoAgent, "add_datasource") as mock_add_datasource:
                    init_app_agent()
                    mock_add_datasource.assert_called_once_with("dj_datasource")
                    mock_django_datasource.assert_called_once()

    def test_should_add_datasource_not_called_when_no_auto_added_asked(self):
        with override_settings(**self.dj_options, FOREST_AUTO_ADD_DJANGO_DATASOURCE=False):
            with patch("forestadmin.django_agent.apps.DjangoDatasource") as mock_django_datasource:
                with patch.object(DjangoAgent, "add_datasource") as mock_add_datasource:
                    init_app_agent()
                    mock_add_datasource.assert_not_called()
                    mock_django_datasource.assert_not_called()

    def test_should_call_customize_fn_when_setting_is_function(self):
        def customize_fn(agent):
            pass

        spy_customize_fn = Mock(customize_fn, wraps=customize_fn)

        with override_settings(**{**self.dj_options, "FOREST_CUSTOMIZE_FUNCTION": spy_customize_fn}):
            agent = init_app_agent()
            spy_customize_fn.assert_called_once_with(agent)

    def test_should_call_customize_fn_when_setting_is_coroutine(self):
        async def customize_fn(agent):
            pass

        spy_customize_fn = AsyncMock(customize_fn, wraps=customize_fn)

        with override_settings(**{**self.dj_options, "FOREST_CUSTOMIZE_FUNCTION": spy_customize_fn}):
            agent = init_app_agent()
            spy_customize_fn.assert_awaited_once_with(agent)

    def test_should_call_customize_fn_and_return_None_when_error_in_customize_fn(self):
        customizer_param = {"agent": None}

        def customizer(agent):
            customizer_param["agent"] = agent
            1 / 0

        spy_customize_fn = Mock(wraps=customizer)

        with override_settings(**{**self.dj_options, "FOREST_CUSTOMIZE_FUNCTION": spy_customize_fn}):
            agent = init_app_agent()
            spy_customize_fn.assert_called_once_with(customizer_param["agent"])
            self.assertIsNone(agent)

    def test_should_call_customize_fn_when_param_is_a_string(self):
        def customizer(agent):
            pass

        with patch("test_app.forest_admin.customize_agent", wraps=customizer) as mock_customizer:
            with override_settings(
                **{**self.dj_options, "FOREST_CUSTOMIZE_FUNCTION": "test_app.forest_admin.customize_agent"}
            ):
                agent = init_app_agent()
                mock_customizer.assert_called_once_with(agent)

    def test_should_return_None_when_error_in_customize_fn_import_from_str(self):
        with override_settings(
            **{**self.dj_options, "FOREST_CUSTOMIZE_FUNCTION": "test_app.forest_admin.customize_agent_import_error"}
        ):
            agent = init_app_agent()
            self.assertIsNone(agent)

    def test_should_call_agent_start_when_everything_work_well_and_launch_as_server(self):
        with override_settings(**self.dj_options):
            with patch("forestadmin.django_agent.apps.is_launch_as_server", return_value=True):
                with patch("forestadmin.django_agent.apps.create_agent", wraps=create_agent) as spy_create_agent:
                    with patch("forestadmin.django_agent.agent.DjangoAgent.start") as mock_start:
                        agent = init_app_agent()
                        spy_create_agent.assert_called_once()
                        mock_start.assert_called_once()
                        self.assertIsNotNone(agent)

    def test_should_not_initialize_agent_when_not_launch_as_server(self):
        with override_settings(**self.dj_options):
            with patch("forestadmin.django_agent.apps.create_agent") as mock_create_agent:
                with patch("forestadmin.django_agent.apps.is_launch_as_server", return_value=False):
                    agent = init_app_agent()
                    mock_create_agent.assert_not_called()
                    self.assertIsNone(agent)

    def test_should_not_call_agent_start_when_error_during_customize_fn(self):
        with override_settings(
            **{**self.dj_options, "FOREST_CUSTOMIZE_FUNCTION": "test_app.forest_admin.customize_agent_import_error"}
        ):
            with patch("forestadmin.django_agent.agent.DjangoAgent.start") as mock_start:
                with patch("forestadmin.django_agent.apps.is_launch_as_server", return_value=True):
                    agent = init_app_agent()
                    mock_start.assert_not_called()
                    self.assertIsNone(agent)


class TestDjangoAgentCreationWaiterThread(DjangoTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.dj_options = {
            "FOREST_ENV_SECRET": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
            "FOREST_AUTH_SECRET": "de1s5LAbFFAPRvCJQTLb",
        }

    def test_app_ready_should_launch_wait_and_launch_thread(self):
        with override_settings(**self.dj_options):
            with patch("forestadmin.django_agent.apps.is_launch_as_server", return_value=True):
                with patch("forestadmin.django_agent.apps.threading.Thread") as mock_thread:
                    app = apps.get_app_config("django_agent")
                    app.ready()
                    mock_thread.assert_called_once_with(name=ANY, target=app._wait_for_all_apps_ready_and_launch_agent)
                    mock_thread.return_value.start.assert_called_once()

    def test_app_ready_should_wait_signal_to_launch_agent(self):
        with override_settings(**self.dj_options):
            with patch("forestadmin.django_agent.apps.init_app_agent", wraps=init_app_agent) as mock_init_app_agent:
                apps.ready_event = threading.Event()
                app = apps.get_app_config("django_agent")
                threading.Timer(0.1, lambda: apps.ready_event.set()).start()
                app.ready()
                apps.ready_event.wait()
                time.sleep(0.1)
                mock_init_app_agent.assert_called()

    def test_waiter_fn_should_warn_when_waiting_time_too_long(self):
        with override_settings(**self.dj_options):
            with patch("forestadmin.django_agent.apps.init_app_agent", wraps=init_app_agent) as mock_init_app_agent:
                with patch("forestadmin.django_agent.apps.ForestLogger") as mock_logger:
                    apps.ready_event = threading.Event()
                    app = apps.get_app_config("django_agent")
                    threading.Timer(0.8, lambda: apps.ready_event.set()).start()
                    with patch.object(app, "_waiter_timeout", 0.4):
                        app._wait_for_all_apps_ready_and_launch_agent()
                    apps.ready_event.wait()
                    time.sleep(0.1)
                    mock_init_app_agent.assert_called()
                    mock_logger.log.assert_called_with(
                        "warning",
                        "Django 'apps.ready_event' never set after 0.40 seconds. Trying to launch agent anyway.",
                    )
