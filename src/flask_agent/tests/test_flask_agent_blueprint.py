import asyncio
from unittest import TestCase
from unittest.mock import ANY, AsyncMock, patch

from flask import Flask
from forestadmin.agent_toolkit.utils.context import Request, RequestMethod, Response
from forestadmin.flask_agent.agent import create_agent


class TestFlaskAgentBlueprint(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()
        cls.mocked_resources = {}
        for key in [
            "native_query",
            "capabilities",
            "authentication",
            "crud",
            "crud_related",
            "stats",
            "actions",
            "collection_charts",
            "datasource_charts",
        ]:
            cls.mocked_resources[key] = AsyncMock()
            cls.mocked_resources[key].dispatch = AsyncMock(
                return_value=Response(200, '{"mock": "ok"}', headers={"content-type": "application/json"})
            )

        cls.app = Flask(__name__)
        cls.app.config.update(
            {
                "FOREST_ENV_SECRET": "da4fc9331a68a18c2262154c74d9acb22f335724c8f2a510f8df187fa808703e",
                "FOREST_AUTH_SECRET": "fake",
            }
        )
        patch(
            "forestadmin.agent_toolkit.agent.Agent.get_resources",
            return_value=cls.mocked_resources,
            new_callable=AsyncMock,
        ).start()

        cls.agent = create_agent(cls.app)
        cls.client = cls.app.test_client()

    def test_index(self):
        response = self.client.get("/forest")
        assert response.status_code == 200
        assert response.json is None

    def test_capabilities(self):
        response = self.client.post(
            "/forest/_internal/capabilities?timezone=Europe%2FParis",
            json={"collectionNames": ["app_test"]},
        )
        assert response.status_code == 200
        assert response.json == {"mock": "ok"}
        self.mocked_resources["capabilities"].dispatch.assert_awaited()
        call_args = self.mocked_resources["capabilities"].dispatch.await_args.args
        self.assertEqual(call_args[1], "capabilities")
        headers = {**call_args[0].headers}
        del headers["User-Agent"]
        call_args[0].headers = headers
        self.assertEqual(
            call_args[0],
            Request(
                RequestMethod.POST,
                body={"collectionNames": ["app_test"]},
                query={"timezone": "Europe/Paris"},
                headers={
                    "Host": "localhost",
                    "Content-Type": "application/json",
                    "Content-Length": "33",
                },
                client_ip="127.0.0.1",
            ),
        )

    def test_native_query(self):
        response = self.client.post(
            "/forest/_internal/native_query?timezone=Europe%2FParis",
            json={
                "connectionName": "django",
                "contextVariables": {},
                "query": "select status as key, sum(amount) as value from order group by key",
                "type": "Pie",
            },
        )
        assert response.status_code == 200
        assert response.json == {"mock": "ok"}
        self.mocked_resources["native_query"].dispatch.assert_awaited()
        call_args = self.mocked_resources["native_query"].dispatch.await_args.args
        self.assertEqual(call_args[1], "native_query")
        headers = {**call_args[0].headers}
        del headers["User-Agent"]
        call_args[0].headers = headers
        self.assertEqual(
            call_args[0],
            Request(
                RequestMethod.POST,
                body={
                    "connectionName": "django",
                    "contextVariables": {},
                    "query": "select status as key, sum(amount) as value from order group by key",
                    "type": "Pie",
                },
                query={"timezone": "Europe/Paris"},
                headers={
                    "Host": "localhost",
                    "Content-Type": "application/json",
                    "Content-Length": "146",
                },
                client_ip="127.0.0.1",
            ),
        )

    def test_hook_load(self):
        response = self.client.post("/forest/_actions/customer/1/action_name/hooks/load")
        assert response.status_code == 200
        assert response.json == {"mock": "ok"}
        self.loop.run_until_complete(self.agent.get_resources())["actions"].dispatch.assert_called()

    def test_hook_change(self):
        response = self.client.post("/forest/_actions/customer/1/action_name/hooks/change")
        assert response.status_code == 200
        assert response.json == {"mock": "ok"}
        self.loop.run_until_complete(self.agent.get_resources())["actions"].dispatch.assert_called()

    def test_hook_search(self):
        response = self.client.post("/forest/_actions/customer/1/action_name/hooks/search")
        assert response.status_code == 200
        assert response.json == {"mock": "ok"}
        self.loop.run_until_complete(self.agent.get_resources())["actions"].dispatch.assert_called()

    def test_action(self):
        response = self.client.post("/forest/_actions/customer/1/action_name")
        assert response.status_code == 200
        assert response.json == {"mock": "ok"}
        self.loop.run_until_complete(self.agent.get_resources())["actions"].dispatch.assert_called()

    def test_auth(self):
        response = self.client.post("/forest/authentication")
        assert response.status_code == 200
        assert response.json == {"mock": "ok"}
        self.loop.run_until_complete(self.agent.get_resources())["authentication"].dispatch.assert_called_with(
            ANY, "authenticate"
        )

    def test_auth_callback(self):
        response = self.client.get("/forest/authentication/callback")
        assert response.status_code == 200
        assert response.json == {"mock": "ok"}
        self.loop.run_until_complete(self.agent.get_resources())["authentication"].dispatch.assert_called_with(
            ANY, "callback"
        )

    def test_stats(self):
        response = self.client.post("/forest/stats/customer")
        assert response.status_code == 200
        assert response.json == {"mock": "ok"}
        self.loop.run_until_complete(self.agent.get_resources())["stats"].dispatch.assert_called()

    def test_count(self):
        response = self.client.get("/forest/customer/count?timezone=Europe%2FParis")
        assert response.status_code == 200
        assert response.json == {"mock": "ok"}
        self.loop.run_until_complete(self.agent.get_resources())["crud"].dispatch.assert_called_with(ANY, "count")

    def test_detail(self):
        response = self.client.get("/forest/customer/1?timezone=Europe%2FParis")
        assert response.status_code == 200
        assert response.json == {"mock": "ok"}
        self.loop.run_until_complete(self.agent.get_resources())["crud"].dispatch.assert_called_with(ANY, "get")

        response = self.client.put("/forest/customer/1?timezone=Europe%2FParis", json={})
        assert response.status_code == 200
        assert response.json == {"mock": "ok"}
        self.loop.run_until_complete(self.agent.get_resources())["crud"].dispatch.assert_called_with(ANY, "update")

        response = self.client.delete("/forest/customer/1?timezone=Europe%2FParis")
        assert response.status_code == 200
        assert response.json == {"mock": "ok"}
        self.loop.run_until_complete(self.agent.get_resources())["crud"].dispatch.assert_called_with(ANY, "delete")

    def test_list(self):
        response = self.client.get("/forest/customer?timezone=Europe%2FParis")
        assert response.status_code == 200
        assert response.json == {"mock": "ok"}
        self.loop.run_until_complete(self.agent.get_resources())["crud"].dispatch.assert_called_with(ANY, "list")

        response = self.client.post("/forest/customer?timezone=Europe%2FParis", json={})
        assert response.status_code == 200
        assert response.json == {"mock": "ok"}
        self.loop.run_until_complete(self.agent.get_resources())["crud"].dispatch.assert_called_with(ANY, "add")

    def test_list_related(self):
        response = self.client.get("/forest/customer/1/relationships/orders?timezone=Europe%2FParis")
        assert response.status_code == 200
        assert response.json == {"mock": "ok"}
        self.loop.run_until_complete(self.agent.get_resources())["crud_related"].dispatch.assert_called_with(
            ANY, "list"
        )

        # attach / add
        response = self.client.post("/forest/customer/1/relationships/orders?timezone=Europe%2FParis", data={})
        assert response.status_code == 200
        assert response.json == {"mock": "ok"}
        self.loop.run_until_complete(self.agent.get_resources())["crud_related"].dispatch.assert_called_with(ANY, "add")

        # detach
        response = self.client.delete("/forest/customer/1/relationships/orders?timezone=Europe%2FParis")
        assert response.status_code == 200
        assert response.json == {"mock": "ok"}
        self.loop.run_until_complete(self.agent.get_resources())["crud_related"].dispatch.assert_called_with(
            ANY, "delete_list"
        )

        # delete related relation item
        response = self.client.delete("/forest/customer/1/relationships/orders?timezone=Europe%2FParis&delete=True")
        assert response.status_code == 200
        assert response.json == {"mock": "ok"}
        self.loop.run_until_complete(self.agent.get_resources())["crud_related"].dispatch.assert_called_with(
            ANY, "delete_list"
        )

        # ??
        response = self.client.put("/forest/customer/1/relationships/orders?timezone=Europe%2FParis")
        assert response.status_code == 200
        assert response.json == {"mock": "ok"}
        self.loop.run_until_complete(self.agent.get_resources())["crud_related"].dispatch.assert_called_with(
            ANY, "update_list"
        )

    def test_count_related(self):
        response = self.client.get("/forest/customer/1/relationships/orders/count?timezone=Europe%2FParis")
        assert response.status_code == 200
        assert response.json == {"mock": "ok"}
        self.loop.run_until_complete(self.agent.get_resources())["crud_related"].dispatch.assert_called_with(
            ANY, "count"
        )

    def test_csv(self):
        response = self.client.get("/forest/customer.csv?timezone=Europe%2FParis")
        assert response.status_code == 200
        self.loop.run_until_complete(self.agent.get_resources())["crud"].dispatch.assert_called_with(ANY, "csv")

    def test_csv_related(self):
        response = self.client.get("/forest/customer/1/relationships/orders.csv?timezone=Europe%2FParis")
        assert response.status_code == 200
        self.loop.run_until_complete(self.agent.get_resources())["crud_related"].dispatch.assert_called_with(ANY, "csv")

    def test_collection_chart(self):
        response = self.client.get("/forest/_charts/customer/test_chart?timezone=Europe%2FParis")
        assert response.status_code == 200
        self.loop.run_until_complete(self.agent.get_resources())["collection_charts"].dispatch.assert_called_with(
            ANY, "list"
        )

        response = self.client.post("/forest/_charts/customer/test_chart?timezone=Europe%2FParis")
        assert response.status_code == 200
        self.loop.run_until_complete(self.agent.get_resources())["collection_charts"].dispatch.assert_called_with(
            ANY, "add"
        )

    def test_datasource_chart(self):
        response = self.client.get("/forest/_charts/test_chart?timezone=Europe%2FParis")
        assert response.status_code == 200
        self.loop.run_until_complete(self.agent.get_resources())["datasource_charts"].dispatch.assert_called_with(
            ANY, "list"
        )

        response = self.client.post("/forest/_charts/test_chart?timezone=Europe%2FParis")
        assert response.status_code == 200
        self.loop.run_until_complete(self.agent.get_resources())["datasource_charts"].dispatch.assert_called_with(
            ANY, "add"
        )

    def test_invalidate_cache(self):
        with patch.object(self.agent._permission_service, "invalidate_cache") as mocked_invalidate_cache:
            response = self.client.post("/forest/scope-cache-invalidation")
            mocked_invalidate_cache.assert_called_with("forest.rendering")
        assert response.status_code == 204
