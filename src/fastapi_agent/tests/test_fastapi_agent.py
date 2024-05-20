import asyncio
from unittest import TestCase
from unittest.mock import patch

from fastapi import FastAPI
from forestadmin.fastapi_agent.agent import FastAPIAgent, create_agent


class TestFlaskAgent(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()
        cls.options = {
            "FOREST_ENV_SECRET": "da4fc9331a68a18c2262154c74d9acb22f335724c8f2a510f8df187fa808703e",
            "FOREST_AUTH_SECRET": "fake",
        }

    def setUp(self) -> None:
        self.fastapi_app = FastAPI()

    def test_create_agent_should_return_an_fastapi_agent(self):
        agent = create_agent(self.fastapi_app, self.options)
        self.assertTrue(isinstance(agent, FastAPIAgent))
        self.assertEqual(agent.options["auth_secret"], "fake")
        self.assertEqual(agent.options["env_secret"], self.options["FOREST_ENV_SECRET"])

    def test_start_should_await_parent_start(self):
        agent = create_agent(self.fastapi_app, self.options)

        with patch.object(agent, "_start", wraps=agent._start) as spy_parent_start:
            self.loop.run_until_complete(agent.start())
            spy_parent_start.assert_awaited_once()

    def test_router_is_correctly_mount(self):
        agent = create_agent(self.fastapi_app, self.options)

        urls_routes = {}
        for route in agent._app.router.routes:
            if urls_routes.get(route.path) is None:  # type:ignore
                urls_routes[route.path] = set()  # type:ignore

            for method in route.methods:  # type:ignore
                if method != "HEAD":
                    urls_routes[route.path].add(method)  # type:ignore

        urls_routes_lst = [(route, methods) for route, methods in urls_routes.items()]

        # global (6)
        self.assertIn(("/forest", {"GET"}), urls_routes_lst)
        self.assertIn(("/forest/authentication/callback", {"GET"}), urls_routes_lst)
        self.assertIn(("/forest/scope-cache-invalidation", {"POST"}), urls_routes_lst)
        self.assertIn(("/forest/stats/{collection_name}", {"POST"}), urls_routes_lst)
        self.assertIn(("/forest/_charts/{collection_name}/{chart_name}", {"GET", "POST"}), urls_routes_lst)
        self.assertIn(("/forest/_charts/{chart_name}", {"POST", "GET"}), urls_routes_lst)

        # authentication (2)
        self.assertIn(("/forest/authentication", {"POST"}), urls_routes_lst)
        self.assertIn(("/forest/authentication/callback", {"GET"}), urls_routes_lst)

        # crud (4)
        self.assertIn(("/forest/{collection_name}.csv", {"GET"}), urls_routes_lst)
        self.assertIn(("/forest/{collection_name}", {"GET", "POST", "DELETE"}), urls_routes_lst)
        self.assertIn(("/forest/{collection_name}/count", {"GET"}), urls_routes_lst)
        self.assertIn(("/forest/{collection_name}/{pks}", {"GET", "PUT", "DELETE"}), urls_routes_lst)

        # crud related (3)
        self.assertIn(("/forest/{collection_name}/{pks}/relationships/{relation_name}.csv", {"GET"}), urls_routes_lst)
        self.assertIn(
            ("/forest/{collection_name}/{pks}/relationships/{relation_name}", {"GET", "POST", "DELETE", "PUT"}),
            urls_routes_lst,
        )
        self.assertIn(("/forest/{collection_name}/{pks}/relationships/{relation_name}/count", {"GET"}), urls_routes_lst)

        # action (4)
        self.assertIn(("/forest/_actions/{collection_name}/{action_name:int}/{slug}", {"POST"}), urls_routes_lst)
        self.assertIn(
            ("/forest/_actions/{collection_name}/{action_name:int}/{slug}/hooks/load", {"POST"}), urls_routes_lst
        )
        self.assertIn(
            ("/forest/_actions/{collection_name}/{action_name:int}/{slug}/hooks/change", {"POST"}), urls_routes_lst
        )
        self.assertIn(
            ("/forest/_actions/{collection_name}/{action_name:int}/{slug}/hooks/search", {"POST"}), urls_routes_lst
        )
