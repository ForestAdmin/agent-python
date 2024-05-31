import asyncio
from unittest import TestCase
from unittest.mock import ANY, AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from forestadmin.agent_toolkit.utils.context import Response
from forestadmin.fastapi_agent.agent import create_agent
from forestadmin.fastapi_agent.settings import ForestFastAPISettings


class TestFastApiRouting(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()
        cls.mocked_resources = {}
        for key in [
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

        cls.app = FastAPI()
        patch(
            "forestadmin.agent_toolkit.agent.Agent.get_resources",
            return_value=cls.mocked_resources,
            new_callable=AsyncMock,
        ).start()

        cls.agent = create_agent(
            cls.app,
            ForestFastAPISettings(
                env_secret="da4fc9331a68a18c2262154c74d9acb22f335724c8f2a510f8df187fa808703e",
                auth_secret="fake",
                schema_path="/tmp/.forestadmin.json",
            ),
        )
        cls.client = TestClient(cls.app)


class TestFastApiRoutingWelcome(TestFastApiRouting):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.stats_dispatch_mock: AsyncMock = cls.loop.run_until_complete(cls.agent.get_resources())["stats"].dispatch
        cls.collection_charts_dispatch_mock: AsyncMock = cls.loop.run_until_complete(cls.agent.get_resources())[
            "collection_charts"
        ].dispatch
        cls.datasource_charts_dispatch_mock: AsyncMock = cls.loop.run_until_complete(cls.agent.get_resources())[
            "datasource_charts"
        ].dispatch

    def test_index(self):
        response = self.client.get("/forest")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")

    def test_stats(self):
        response = self.client.post("/forest/stats/customer")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"mock": "ok"})
        self.stats_dispatch_mock.assert_any_call(ANY)

    def test_collection_chart_get(self):
        response = self.client.get("/forest/_charts/customer/test_chart?timezone=Europe%2FParis")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"mock": "ok"})
        self.collection_charts_dispatch_mock.assert_called_with(ANY)

    def test_collection_chart_post(self):
        response = self.client.post("/forest/_charts/customer/test_chart?timezone=Europe%2FParis")
        self.assertEqual(response.json(), {"mock": "ok"})
        self.assertEqual(response.status_code, 200)
        self.collection_charts_dispatch_mock.assert_called_with(ANY)

    def test_datasource_chart_get(self):
        response = self.client.get("/forest/_charts/test_chart?timezone=Europe%2FParis")
        self.assertEqual(response.json(), {"mock": "ok"})
        self.assertEqual(response.status_code, 200)
        self.datasource_charts_dispatch_mock.assert_called_with(ANY)

    def test_datasource_chart_post(self):
        response = self.client.post("/forest/_charts/test_chart?timezone=Europe%2FParis")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"mock": "ok"})
        self.datasource_charts_dispatch_mock.assert_called_with(ANY)

        with patch.object(self.agent._permission_service, "invalidate_cache") as mocked_invalidate_cache:
            response = self.client.post("/forest/scope-cache-invalidation")
            mocked_invalidate_cache.assert_called_with("forest.scopes")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")


class TestFastApiRoutingAction(TestFastApiRouting):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.action_dispatch_mock: AsyncMock = cls.loop.run_until_complete(cls.agent.get_resources())["actions"].dispatch

    def test_hook_load(self):
        response = self.client.post("/forest/_actions/customer/1/action_name/hooks/load")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"mock": "ok"})
        self.action_dispatch_mock.assert_any_call(ANY, "hook")

    def test_hook_change(self):
        response = self.client.post("/forest/_actions/customer/1/action_name/hooks/change")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"mock": "ok"})
        self.action_dispatch_mock.assert_any_call(ANY, "hook")

    def test_hook_search(self):
        response = self.client.post("/forest/_actions/customer/1/action_name/hooks/search")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"mock": "ok"})
        self.action_dispatch_mock.assert_any_call(ANY, "hook")

    def test_action(self):
        response = self.client.post("/forest/_actions/customer/1/action_name")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"mock": "ok"})
        self.action_dispatch_mock.assert_any_call(ANY, "execute")


class TestFastApiRoutingAuthentication(TestFastApiRouting):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.authentication_dispatch_mock: AsyncMock = cls.loop.run_until_complete(cls.agent.get_resources())[
            "authentication"
        ].dispatch

    def test_auth(self):
        response = self.client.post("/forest/authentication")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"mock": "ok"})
        self.authentication_dispatch_mock.assert_any_call(ANY, "authenticate")

    def test_auth_callback(self):
        response = self.client.get("/forest/authentication/callback")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"mock": "ok"})
        self.authentication_dispatch_mock.assert_any_call(ANY, "callback")


class TestFastApiRoutingCRUD(TestFastApiRouting):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.crud_dispatch_mock: AsyncMock = cls.loop.run_until_complete(cls.agent.get_resources())["crud"].dispatch

    def test_list_list(self):
        response = self.client.get("/forest/customer?timezone=Europe%2FParis")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"mock": "ok"})
        self.crud_dispatch_mock.assert_called_with(ANY, "list")

    def test_list_create(self):
        response = self.client.post("/forest/customer?timezone=Europe%2FParis", json={})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"mock": "ok"})
        self.crud_dispatch_mock.assert_called_with(ANY, "add")

    def test_list_del(self):
        response = self.client.delete("/forest/customer?timezone=Europe%2FParis")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"mock": "ok"})
        self.crud_dispatch_mock.assert_called_with(ANY, "delete_list")

    def test_csv(self):
        response = self.client.get("/forest/customer.csv?timezone=Europe%2FParis")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"mock": "ok"})
        self.crud_dispatch_mock.assert_called_with(ANY, "csv")

    def test_count(self):
        response = self.client.get("/forest/customer/count?timezone=Europe%2FParis")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"mock": "ok"})
        self.crud_dispatch_mock.assert_called_with(ANY, "count")

    def test_detail_edit(self):
        response = self.client.put("/forest/customer/1?timezone=Europe%2FParis", json={})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"mock": "ok"})
        self.crud_dispatch_mock.assert_called_with(ANY, "update")

    def test_detail_get(self):
        response = self.client.get("/forest/customer/1?timezone=Europe%2FParis")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"mock": "ok"})
        self.crud_dispatch_mock.assert_called_with(ANY, "get")

    def test_detail_del(self):
        response = self.client.delete("/forest/customer/1?timezone=Europe%2FParis")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"mock": "ok"})
        self.crud_dispatch_mock.assert_called_with(ANY, "delete")


class TestFastApiRoutingCRUDRelated(TestFastApiRouting):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.crud_related_dispatch_mock: AsyncMock = cls.loop.run_until_complete(cls.agent.get_resources())[
            "crud_related"
        ].dispatch

    def test_list_related_list(self):
        response = self.client.get("/forest/customer/1/relationships/orders?timezone=Europe%2FParis")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"mock": "ok"})
        self.crud_related_dispatch_mock.assert_called_with(ANY, "list")

    def test_list_related_add(self):
        # attach / add
        response = self.client.post("/forest/customer/1/relationships/orders?timezone=Europe%2FParis", data={})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"mock": "ok"})
        self.crud_related_dispatch_mock.assert_called_with(ANY, "add")

    def test_list_related_delete_list(self):
        # detach
        response = self.client.delete("/forest/customer/1/relationships/orders?timezone=Europe%2FParis")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"mock": "ok"})
        self.crud_related_dispatch_mock.assert_called_with(ANY, "delete_list")

        # delete related relation item
        response = self.client.delete("/forest/customer/1/relationships/orders?timezone=Europe%2FParis&delete=True")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"mock": "ok"})
        self.crud_related_dispatch_mock.assert_called_with(ANY, "delete_list")

    def test_list_related_update_list(self):
        # ??
        response = self.client.put("/forest/customer/1/relationships/orders?timezone=Europe%2FParis")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"mock": "ok"})
        self.crud_related_dispatch_mock.assert_called_with(ANY, "update_list")

    def test_count_related(self):
        response = self.client.get("/forest/customer/1/relationships/orders/count?timezone=Europe%2FParis")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"mock": "ok"})
        self.crud_related_dispatch_mock.assert_called_with(ANY, "count")

    def test_csv_related(self):
        response = self.client.get("/forest/customer/1/relationships/orders.csv?timezone=Europe%2FParis")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"mock": "ok"})
        self.crud_related_dispatch_mock.assert_called_with(ANY, "csv")
