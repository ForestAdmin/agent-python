import sys
from unittest import TestCase
from unittest.mock import ANY, PropertyMock, patch

if sys.version_info >= (3, 8):
    from unittest.mock import AsyncMock
else:
    from mock import AsyncMock

from flask import Flask
from forestadmin.agent_toolkit.utils.context import Response
from forestadmin.flask_agent.agent import build_agent


class TestFlaskAgentBlueprint(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
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

        cls.app = Flask(__name__)
        patch(
            "forestadmin.agent_toolkit.agent.Agent.resources",
            return_value=cls.mocked_resources,
            new_callable=PropertyMock,
        ).start()
        cls.agent = build_agent(
            {
                "env_secret": "fake",
                "auth_secret": "fake",
                "agent_url": "fake",
            }
        )
        cls.agent.start = AsyncMock()
        cls.agent.register_blueprint(cls.app)
        cls.client = cls.app.test_client()

    def test_index(self):
        response = self.client.get("/forest")
        assert response.status_code == 200
        assert response.text == ""

    def test_hook_load(self):
        response = self.client.post("/forest/_actions/customer/1/action_name/hooks/load")
        assert response.status_code == 200
        assert response.json == {"mock": "ok"}
        self.agent.resources["actions"].dispatch.assert_called()

    def test_hook_change(self):
        response = self.client.post("/forest/_actions/customer/1/action_name/hooks/change")
        assert response.status_code == 200
        assert response.json == {"mock": "ok"}
        self.agent.resources["actions"].dispatch.assert_called()

    def test_action(self):
        response = self.client.post("/forest/_actions/customer/1/action_name")
        assert response.status_code == 200
        assert response.json == {"mock": "ok"}
        self.agent.resources["actions"].dispatch.assert_called()

    def test_auth(self):
        response = self.client.post("/forest/authentication")
        assert response.status_code == 200
        assert response.json == {"mock": "ok"}
        self.agent.resources["authentication"].dispatch.assert_called_with(ANY, "authenticate")

    def test_auth_callback(self):
        response = self.client.get("/forest/authentication/callback")
        assert response.status_code == 200
        assert response.json == {"mock": "ok"}
        self.agent.resources["authentication"].dispatch.assert_called_with(ANY, "callback")

    def test_stats(self):
        response = self.client.post("/forest/stats/customer")
        assert response.status_code == 200
        assert response.json == {"mock": "ok"}
        self.agent.resources["stats"].dispatch.assert_called()

    def test_count(self):
        response = self.client.get("/forest/customer/count?timezone=Europe%2FParis")
        assert response.status_code == 200
        assert response.json == {"mock": "ok"}
        self.agent.resources["crud"].dispatch.assert_called_with(ANY, "count")

    def test_detail(self):
        response = self.client.get("/forest/customer/1?timezone=Europe%2FParis")
        assert response.status_code == 200
        assert response.json == {"mock": "ok"}
        self.agent.resources["crud"].dispatch.assert_called_with(ANY, "get")

        response = self.client.put("/forest/customer/1?timezone=Europe%2FParis", json={})
        assert response.status_code == 200
        assert response.json == {"mock": "ok"}
        self.agent.resources["crud"].dispatch.assert_called_with(ANY, "update")

        response = self.client.delete("/forest/customer/1?timezone=Europe%2FParis")
        assert response.status_code == 200
        assert response.json == {"mock": "ok"}
        self.agent.resources["crud"].dispatch.assert_called_with(ANY, "delete")

    def test_list(self):
        response = self.client.get("/forest/customer?timezone=Europe%2FParis")
        assert response.status_code == 200
        assert response.json == {"mock": "ok"}
        self.agent.resources["crud"].dispatch.assert_called_with(ANY, "list")

        response = self.client.post("/forest/customer?timezone=Europe%2FParis", json={})
        assert response.status_code == 200
        assert response.json == {"mock": "ok"}
        self.agent.resources["crud"].dispatch.assert_called_with(ANY, "add")

    def test_list_related(self):
        response = self.client.get("/forest/customer/1/relationships/orders?timezone=Europe%2FParis")
        assert response.status_code == 200
        assert response.json == {"mock": "ok"}
        self.agent.resources["crud_related"].dispatch.assert_called_with(ANY, "list")

        # attach / add
        response = self.client.post("/forest/customer/1/relationships/orders?timezone=Europe%2FParis", data={})
        assert response.status_code == 200
        assert response.json == {"mock": "ok"}
        self.agent.resources["crud_related"].dispatch.assert_called_with(ANY, "add")

        # detach
        response = self.client.delete("/forest/customer/1/relationships/orders?timezone=Europe%2FParis")
        assert response.status_code == 200
        assert response.json == {"mock": "ok"}
        self.agent.resources["crud_related"].dispatch.assert_called_with(ANY, "delete_list")

        # delete related relation item
        response = self.client.delete("/forest/customer/1/relationships/orders?timezone=Europe%2FParis&delete=True")
        assert response.status_code == 200
        assert response.json == {"mock": "ok"}
        self.agent.resources["crud_related"].dispatch.assert_called_with(ANY, "delete_list")

        # ??
        response = self.client.put("/forest/customer/1/relationships/orders?timezone=Europe%2FParis")
        assert response.status_code == 200
        assert response.json == {"mock": "ok"}
        self.agent.resources["crud_related"].dispatch.assert_called_with(ANY, "update_list")

    def test_count_related(self):
        response = self.client.get("/forest/customer/1/relationships/orders/count?timezone=Europe%2FParis")
        assert response.status_code == 200
        assert response.json == {"mock": "ok"}
        self.agent.resources["crud_related"].dispatch.assert_called_with(ANY, "count")

    def test_csv(self):
        response = self.client.get("/forest/customer.csv?timezone=Europe%2FParis")
        assert response.status_code == 200
        self.agent.resources["crud"].dispatch.assert_called_with(ANY, "csv")

    def test_csv_related(self):
        response = self.client.get("/forest/customer/1/relationships/orders.csv?timezone=Europe%2FParis")
        assert response.status_code == 200
        self.agent.resources["crud_related"].dispatch.assert_called_with(ANY, "csv")

    def test_collection_chart(self):
        response = self.client.get("/forest/_charts/customer/test_chart?timezone=Europe%2FParis")
        assert response.status_code == 200
        self.agent.resources["collection_charts"].dispatch.assert_called_with(ANY, "list")

        response = self.client.post("/forest/_charts/customer/test_chart?timezone=Europe%2FParis")
        assert response.status_code == 200
        self.agent.resources["collection_charts"].dispatch.assert_called_with(ANY, "add")

    def test_datasource_chart(self):
        response = self.client.get("/forest/_charts/test_chart?timezone=Europe%2FParis")
        assert response.status_code == 200
        self.agent.resources["datasource_charts"].dispatch.assert_called_with(ANY, "list")

        response = self.client.post("/forest/_charts/test_chart?timezone=Europe%2FParis")
        assert response.status_code == 200
        self.agent.resources["datasource_charts"].dispatch.assert_called_with(ANY, "add")
