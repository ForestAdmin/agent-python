import asyncio
import json
from io import BytesIO
from unittest.mock import ANY, AsyncMock, patch

from django.apps.registry import apps
from django.test import TestCase
from forestadmin.agent_toolkit.utils.context import FileResponse, Request, RequestMethod, Response
from forestadmin.django_agent.agent import DjangoAgent


class TestDjangoAgentRoutes(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()
        cls.django_agent: DjangoAgent = apps.get_app_config("django_agent").get_agent()

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

            def get_response(request, method_name=None):
                ret = Response(200, '{"mock": "ok"}', headers={"content-type": "application/json"})
                if method_name == "csv":
                    ret = FileResponse(file=BytesIO(b"test file"), name="text.csv", mimetype="text/csv;charset=UTF-8")
                return ret

            cls.mocked_resources[key] = AsyncMock()
            cls.mocked_resources[key].dispatch = AsyncMock(side_effect=get_response)

        patch.object(
            cls.django_agent, "get_resources", new_callable=AsyncMock, return_value=cls.mocked_resources
        ).start()

        cls.conf_prefix = cls.django_agent.options.get("prefix", "")
        # here the same rules as in urls.py
        if len(cls.conf_prefix) > 0 and cls.conf_prefix[-1] != "/":
            cls.conf_prefix = f"{cls.conf_prefix}/"
        if len(cls.conf_prefix) > 0 and cls.conf_prefix[0] == "/":
            cls.conf_prefix = f"{cls.conf_prefix[1:]}"

        patch("forestadmin.django_agent.apps.is_launch_as_server", return_value=True).start()

        super().setUpClass()


class TestDjangoAgentGenericRoutes(TestDjangoAgentRoutes):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

    def test_index(self):
        response = self.client.get(f"/{self.conf_prefix}forest/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"")

    def test_scope_cache_invalidation(self):
        response = self.client.get(
            f"/{self.conf_prefix}forest/scope-cache-invalidation",
            HTTP_X_FORWARDED_FOR="179.114.131.49",
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")


class TestDjangoAgentAuthenticationRoutes(TestDjangoAgentRoutes):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.authentication_resource = cls.loop.run_until_complete(cls.django_agent.get_resources())["authentication"]

    def test_authenticate(self):
        response = self.client.post(
            f"/{self.conf_prefix}forest/authentication",
            json.dumps({"post_attr": "post_value"}),
            content_type="application/json",
            HTTP_X_FORWARDED_FOR="179.114.131.49",
        )
        self.authentication_resource.dispatch.assert_any_await(ANY, "authenticate")
        request_param: Request = self.authentication_resource.dispatch.await_args[0][0]
        self.assertEqual(request_param.method, RequestMethod.POST)
        self.assertEqual(request_param.client_ip, "179.114.131.49")
        self.assertEqual(request_param.body, {"post_attr": "post_value"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"mock": "ok"})
        self.assertEqual(response.has_header("content-type"), True)
        self.assertEqual(response.headers["content-type"], "application/json")
        self.authentication_resource.dispatch.reset_mock()

    def test_callback(self):
        response = self.client.post(
            f"/{self.conf_prefix}forest/authentication/callback",
            json.dumps({"post_attr": "post_value"}),
            content_type="application/json",
            HTTP_X_FORWARDED_FOR="179.114.131.49",
        )
        self.authentication_resource.dispatch.assert_any_await(ANY, "callback")
        request_param: Request = self.authentication_resource.dispatch.await_args[0][0]
        self.assertEqual(request_param.method, RequestMethod.POST)
        self.assertEqual(request_param.client_ip, "179.114.131.49")
        self.assertEqual(request_param.body, {"post_attr": "post_value"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"mock": "ok"})
        self.assertEqual(response.has_header("content-type"), True)
        self.assertEqual(response.headers["content-type"], "application/json")
        self.authentication_resource.dispatch.reset_mock()


class TestDjangoAgentActionsRoutes(TestDjangoAgentRoutes):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.action_resource = cls.loop.run_until_complete(cls.django_agent.get_resources())["actions"]

    def test_hook_load(self):
        response = self.client.post(
            f"/{self.conf_prefix}forest/_actions/customer/1/action_name/hooks/load",
            json.dumps({"post_attr": "post_value"}),
            content_type="application/json",
            HTTP_X_FORWARDED_FOR="179.114.131.49",
        )
        self.action_resource.dispatch.assert_any_await(ANY, "hook")
        request_param: Request = self.action_resource.dispatch.await_args[0][0]
        self.assertEqual(request_param.method, RequestMethod.POST)
        self.assertEqual(request_param.client_ip, "179.114.131.49")
        self.assertEqual(request_param.body, {"post_attr": "post_value"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"mock": "ok"})
        self.assertEqual(response.has_header("content-type"), True)
        self.assertEqual(response.headers["content-type"], "application/json")
        self.action_resource.dispatch.reset_mock()

    def test_hook_change(self):
        response = self.client.post(
            f"/{self.conf_prefix}forest/_actions/customer/1/action_name/hooks/change",
            json.dumps({"post_attr": "post_value"}),
            content_type="application/json",
            HTTP_X_FORWARDED_FOR="179.114.131.49",
        )
        self.action_resource.dispatch.assert_any_await(ANY, "hook")
        request_param: Request = self.action_resource.dispatch.await_args[0][0]
        self.assertEqual(request_param.method, RequestMethod.POST)
        self.assertEqual(request_param.client_ip, "179.114.131.49")
        self.assertEqual(request_param.body, {"post_attr": "post_value"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"mock": "ok"})
        self.assertEqual(response.has_header("content-type"), True)
        self.assertEqual(response.headers["Content-Type"], "application/json")
        self.action_resource.dispatch.reset_mock()

    def test_hook_search(self):
        response = self.client.post(
            f"/{self.conf_prefix}forest/_actions/customer/1/action_name/hooks/search",
            json.dumps({"post_attr": "post_value"}),
            content_type="application/json",
            HTTP_X_FORWARDED_FOR="179.114.131.49",
        )
        self.action_resource.dispatch.assert_any_await(ANY, "hook")
        request_param: Request = self.action_resource.dispatch.await_args[0][0]
        self.assertEqual(request_param.method, RequestMethod.POST)
        self.assertEqual(request_param.client_ip, "179.114.131.49")
        self.assertEqual(request_param.body, {"post_attr": "post_value"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"mock": "ok"})
        self.assertEqual(response.has_header("content-type"), True)
        self.assertEqual(response.headers["Content-Type"], "application/json")
        self.action_resource.dispatch.reset_mock()

    def test_execute(self):
        response = self.client.post(
            f"/{self.conf_prefix}forest/_actions/customer/1/action_name",
            json.dumps({"post_attr": "post_value"}),
            content_type="application/json",
            HTTP_X_FORWARDED_FOR="179.114.131.49",
        )
        self.action_resource.dispatch.assert_any_await(ANY, "execute")
        request_param: Request = self.action_resource.dispatch.await_args[0][0]
        self.assertEqual(request_param.method, RequestMethod.POST)
        self.assertEqual(request_param.client_ip, "179.114.131.49")
        self.assertEqual(request_param.body, {"post_attr": "post_value"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"mock": "ok"})
        self.assertEqual(response.has_header("content-type"), True)
        self.assertEqual(response.headers["content-type"], "application/json")
        self.action_resource.dispatch.reset_mock()


class TestDjangoAgentCrudRoutes(TestDjangoAgentRoutes):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.crud_resource = cls.loop.run_until_complete(cls.django_agent.get_resources())["crud"]

    def test_list(self):
        self.client.get(f"/{self.conf_prefix}forest/customer")
        self.crud_resource.dispatch.assert_any_await(ANY, "list")
        request_param: Request = self.crud_resource.dispatch.await_args[0][0]
        self.assertEqual(request_param.method, RequestMethod.GET)
        self.assertEqual(request_param.query["collection_name"], "customer")

    def test_get(self):
        self.client.get(f"/{self.conf_prefix}forest/customer/12")
        self.crud_resource.dispatch.assert_any_await(ANY, "get")
        request_param: Request = self.crud_resource.dispatch.await_args[0][0]
        self.assertEqual(request_param.method, RequestMethod.GET)
        self.assertEqual(request_param.query["collection_name"], "customer")
        self.assertEqual(request_param.query["pks"], "12")

    def test_count(self):
        self.client.get(f"/{self.conf_prefix}forest/customer/count")
        self.crud_resource.dispatch.assert_any_await(ANY, "count")
        request_param: Request = self.crud_resource.dispatch.await_args[0][0]
        self.assertEqual(request_param.method, RequestMethod.GET)
        self.assertEqual(request_param.query["collection_name"], "customer")

    def test_csv(self):
        response = self.client.get(f"/{self.conf_prefix}forest/customer.csv")
        self.crud_resource.dispatch.assert_any_await(ANY, "csv")
        request_param: Request = self.crud_resource.dispatch.await_args[0][0]
        self.assertEqual(request_param.method, RequestMethod.GET)
        self.assertEqual(request_param.query["collection_name"], "customer")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "text/csv;charset=UTF-8")
        self.assertEqual(response.headers["Content-Disposition"], "attachment; filename=text.csv")
        self.assertEqual(response.content, b"test file")

    def test_add(self):
        self.client.post(
            f"/{self.conf_prefix}forest/customer",
            json.dumps({"post_attr": "post_value"}),
            content_type="application/json",
        )
        self.crud_resource.dispatch.assert_any_await(ANY, "add")
        request_param: Request = self.crud_resource.dispatch.await_args[0][0]
        self.assertEqual(request_param.method, RequestMethod.POST)
        self.assertEqual(request_param.query["collection_name"], "customer")
        self.assertEqual(request_param.body, {"post_attr": "post_value"})

    def test_update(self):
        self.client.put(
            f"/{self.conf_prefix}forest/customer/12",
            json.dumps({"post_attr": "post_value"}),
            content_type="application/json",
        )
        self.crud_resource.dispatch.assert_any_await(ANY, "update")
        request_param: Request = self.crud_resource.dispatch.await_args[0][0]
        self.assertEqual(request_param.method, RequestMethod.PUT)
        self.assertEqual(request_param.query["collection_name"], "customer")
        self.assertEqual(request_param.query["pks"], "12")
        self.assertEqual(request_param.body, {"post_attr": "post_value"})

    def test_delete(self):
        self.client.delete(f"/{self.conf_prefix}forest/customer/12")
        self.crud_resource.dispatch.assert_any_await(ANY, "delete")
        request_param: Request = self.crud_resource.dispatch.await_args[0][0]
        self.assertEqual(request_param.method, RequestMethod.DELETE)
        self.assertEqual(request_param.query["collection_name"], "customer")
        self.assertEqual(request_param.query["pks"], "12")

    def test_delete_list(self):
        self.client.delete(
            f"/{self.conf_prefix}forest/customer",
            json.dumps({"post_attr": "post_value"}),
            content_type="application/json",
        )
        self.crud_resource.dispatch.assert_any_await(ANY, "delete_list")
        request_param: Request = self.crud_resource.dispatch.await_args[0][0]
        self.assertEqual(request_param.method, RequestMethod.DELETE)
        self.assertEqual(request_param.query["collection_name"], "customer")
        self.assertEqual(request_param.body, {"post_attr": "post_value"})


class TestDjangoAgentCrudRelatedRoutes(TestDjangoAgentRoutes):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.crud_related_resource = cls.loop.run_until_complete(cls.django_agent.get_resources())["crud_related"]

    def test_list(self):
        self.client.get(f"/{self.conf_prefix}forest/customer/12/relationships/groups")
        self.crud_related_resource.dispatch.assert_any_await(ANY, "list")
        request_param: Request = self.crud_related_resource.dispatch.await_args[0][0]
        self.assertEqual(request_param.method, RequestMethod.GET)
        self.assertEqual(request_param.query["collection_name"], "customer")
        self.assertEqual(request_param.query["pks"], "12")
        self.assertEqual(request_param.query["relation_name"], "groups")

    def test_count(self):
        self.client.get(f"/{self.conf_prefix}forest/customer/12/relationships/groups/count")
        self.crud_related_resource.dispatch.assert_any_await(ANY, "count")
        request_param: Request = self.crud_related_resource.dispatch.await_args[0][0]
        self.assertEqual(request_param.method, RequestMethod.GET)
        self.assertEqual(request_param.query["collection_name"], "customer")
        self.assertEqual(request_param.query["pks"], "12")
        self.assertEqual(request_param.query["relation_name"], "groups")

    def test_csv(self):
        response = self.client.get(f"/{self.conf_prefix}forest/customer/12/relationships/groups.csv")
        self.crud_related_resource.dispatch.assert_any_await(ANY, "csv")
        request_param: Request = self.crud_related_resource.dispatch.await_args[0][0]
        self.assertEqual(request_param.method, RequestMethod.GET)
        self.assertEqual(request_param.query["collection_name"], "customer")
        self.assertEqual(request_param.query["pks"], "12")
        self.assertEqual(request_param.query["relation_name"], "groups")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "text/csv;charset=UTF-8")
        self.assertEqual(response.headers["Content-Disposition"], "attachment; filename=text.csv")
        self.assertEqual(response.content, b"test file")

    def test_add(self):
        self.client.post(
            f"/{self.conf_prefix}forest/customer/12/relationships/groups",
            json.dumps({"post_attr": "post_value"}),
            content_type="application/json",
        )
        self.crud_related_resource.dispatch.assert_any_await(ANY, "add")
        request_param: Request = self.crud_related_resource.dispatch.await_args[0][0]
        self.assertEqual(request_param.method, RequestMethod.POST)
        self.assertEqual(request_param.query["collection_name"], "customer")
        self.assertEqual(request_param.query["pks"], "12")
        self.assertEqual(request_param.query["relation_name"], "groups")
        self.assertEqual(request_param.body, {"post_attr": "post_value"})

    def test_update(self):
        self.client.put(
            f"/{self.conf_prefix}forest/customer/12/relationships/groups",
            json.dumps({"post_attr": "post_value"}),
            content_type="application/json",
        )
        self.crud_related_resource.dispatch.assert_any_await(ANY, "update_list")
        request_param: Request = self.crud_related_resource.dispatch.await_args[0][0]
        self.assertEqual(request_param.method, RequestMethod.PUT)
        self.assertEqual(request_param.query["collection_name"], "customer")
        self.assertEqual(request_param.query["pks"], "12")
        self.assertEqual(request_param.query["relation_name"], "groups")
        self.assertEqual(request_param.body, {"post_attr": "post_value"})

    def test_delete_list(self):
        self.client.delete(
            f"/{self.conf_prefix}forest/customer/12/relationships/groups",
            json.dumps({"post_attr": "post_value"}),
            content_type="application/json",
        )
        self.crud_related_resource.dispatch.assert_any_await(ANY, "delete_list")
        request_param: Request = self.crud_related_resource.dispatch.await_args[0][0]
        self.assertEqual(request_param.method, RequestMethod.DELETE)
        self.assertEqual(request_param.query["collection_name"], "customer")
        self.assertEqual(request_param.query["pks"], "12")
        self.assertEqual(request_param.query["relation_name"], "groups")
        self.assertEqual(request_param.body, {"post_attr": "post_value"})


class TestDjangoAgentCollectionChartRoutes(TestDjangoAgentRoutes):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.collection_chart_resource = cls.loop.run_until_complete(cls.django_agent.get_resources())[
            "collection_charts"
        ]

    def test_collection_chart(self):
        self.client.post(
            f"/{self.conf_prefix}forest/_charts/customer/first_chart",
            json.dumps({"post_attr": "post_value"}),
            content_type="application/json",
        )
        self.collection_chart_resource.dispatch.assert_any_await(ANY, "add")
        request_param: Request = self.collection_chart_resource.dispatch.await_args[0][0]
        self.assertEqual(request_param.method, RequestMethod.POST)
        self.assertEqual(request_param.query["collection_name"], "customer")
        self.assertEqual(request_param.query["chart_name"], "first_chart")
        self.assertEqual(request_param.body, {"post_attr": "post_value"})


class TestDjangoAgentDatasourceChartRoutes(TestDjangoAgentRoutes):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.datasource_chart_resource = cls.loop.run_until_complete(cls.django_agent.get_resources())[
            "datasource_charts"
        ]

    def test_datasource_chart(self):
        self.client.post(
            f"/{self.conf_prefix}forest/_charts/first_chart",
            json.dumps({"post_attr": "post_value"}),
            content_type="application/json",
        )
        self.datasource_chart_resource.dispatch.assert_any_await(ANY, "add")
        request_param: Request = self.datasource_chart_resource.dispatch.await_args[0][0]
        self.assertEqual(request_param.method, RequestMethod.POST)
        self.assertEqual(request_param.query["chart_name"], "first_chart")
        self.assertEqual(request_param.body, {"post_attr": "post_value"})


class TestDjangoAgentStatRoutes(TestDjangoAgentRoutes):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.stats_resource = cls.loop.run_until_complete(cls.django_agent.get_resources())["stats"]

    def test_stat_list(self):
        self.client.post(
            f"/{self.conf_prefix}forest/stats/customer",
            json.dumps({"post_attr": "post_value"}),
            content_type="application/json",
        )
        self.stats_resource.dispatch.assert_any_await(ANY)
        request_param: Request = self.stats_resource.dispatch.await_args[0][0]
        self.assertEqual(request_param.method, RequestMethod.POST)
        self.assertEqual(request_param.query["collection_name"], "customer")
        self.assertEqual(request_param.body, {"post_attr": "post_value"})
