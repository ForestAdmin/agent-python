import asyncio
from unittest import TestCase
from unittest.mock import AsyncMock, Mock, call, patch

import aiohttp
from forestadmin.agent_toolkit.utils.http import ForestHttpApi, ForestHttpApiException, HttpOptions


class TestForestHttp(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()

        cls.options: HttpOptions = {
            "env_secret": "env_secret",
            "forest_server_url": "http://local.forest.com",
        }

    def test_get_environment_permissions_should_make_correct_call(self):
        with patch.object(ForestHttpApi, "get", new_callable=AsyncMock) as mock_get:
            self.loop.run_until_complete(ForestHttpApi.get_environment_permissions(self.options))

            mock_get.assert_awaited_once_with(
                "http://local.forest.com/liana/v4/permissions/environment", {"forest-secret-key": "env_secret"}
            )

    def test_get_users(self):
        with patch.object(ForestHttpApi, "get", new_callable=AsyncMock) as mock_get:
            self.loop.run_until_complete(ForestHttpApi.get_users(self.options))

            mock_get.assert_awaited_once_with(
                "http://local.forest.com/liana/v4/permissions/users", {"forest-secret-key": "env_secret"}
            )

    def test_get_rendering_permissions(self):
        with patch.object(ForestHttpApi, "get", new_callable=AsyncMock) as mock_get:
            self.loop.run_until_complete(ForestHttpApi.get_rendering_permissions(42, self.options))

            mock_get.assert_awaited_once_with(
                "http://local.forest.com/liana/v4/permissions/renderings/42", {"forest-secret-key": "env_secret"}
            )

    def test_get_open_id_issuer_metadata(self):
        with patch.object(ForestHttpApi, "get", new_callable=AsyncMock) as mock_get:
            self.loop.run_until_complete(ForestHttpApi.get_open_id_issuer_metadata(self.options))

            mock_get.assert_awaited_once_with(
                "http://local.forest.com/oidc/.well-known/openid-configuration", {"forest-secret-key": "env_secret"}
            )

    def test_get_rendering_authorization(self):
        with patch.object(ForestHttpApi, "get", new_callable=AsyncMock) as mock_get:
            self.loop.run_until_complete(ForestHttpApi.get_rendering_authorization(42, "access_token", self.options))

            mock_get.assert_awaited_once_with(
                "http://local.forest.com/liana/v2/renderings/42/authorization",
                {"forest-secret-key": "env_secret", "forest-token": "access_token"},
            )

    def test_schema_should_send_schema_if_server_want_it(self):
        schema = {"meta": {"schemaFileHash": "hash"}}
        with patch.object(
            ForestHttpApi, "post", new_callable=AsyncMock, return_value={"sendSchema": True}
        ) as mock_post:
            self.loop.run_until_complete(ForestHttpApi.send_schema(self.options, schema))
            mock_post.assert_has_awaits(
                [
                    call(
                        "http://local.forest.com/forest/apimaps/hashcheck",
                        {"schemaFileHash": "hash"},
                        {"forest-secret-key": "env_secret", "content-type": "application/json"},
                    ),
                    call(
                        "http://local.forest.com/forest/apimaps",
                        schema,
                        {"forest-secret-key": "env_secret", "content-type": "application/json"},
                    ),
                ]
            )

    def test_schema_should_no_send_schema_if_server_dont_want_it(self):
        schema = {"meta": {"schemaFileHash": "hash"}}
        with patch.object(
            ForestHttpApi, "post", new_callable=AsyncMock, return_value={"sendSchema": False}
        ) as mock_post:
            self.loop.run_until_complete(ForestHttpApi.send_schema(self.options, schema))
            mock_post.assert_has_awaits(
                [
                    call(
                        "http://local.forest.com/forest/apimaps/hashcheck",
                        {"schemaFileHash": "hash"},
                        {"forest-secret-key": "env_secret", "content-type": "application/json"},
                    ),
                ]
            )

    def test_post_should_make_a_post_request_and_return_json(self):
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"ret": True})

        mock_session = Mock()
        mock_session.post = Mock()
        mock_session.post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.post.return_value.__aexit__ = AsyncMock()

        client_session_mock = Mock()
        client_session_mock.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        client_session_mock.return_value.__aexit__ = AsyncMock()

        with patch("forestadmin.agent_toolkit.utils.http.aiohttp.ClientSession", client_session_mock):
            response = self.loop.run_until_complete(
                ForestHttpApi.post("http://addr", {"body": "dict"}, {"headers": "headers"})
            )

            self.assertEqual(response, {"ret": True})

        mock_session.post.assert_called_once_with("http://addr", json={"body": "dict"}, headers={"headers": "headers"})
        mock_response.json.assert_awaited_once()

    def test_post_should_make_a_post_request_and_return_None_if_no_200_answer(self):
        response = Mock()
        response.status = 204

        mock_session = Mock()
        mock_session.post = Mock()
        mock_session.post.return_value.__aenter__ = AsyncMock(return_value=response)
        mock_session.post.return_value.__aexit__ = AsyncMock()

        client_session_mock = Mock()
        client_session_mock.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        client_session_mock.return_value.__aexit__ = AsyncMock()

        with patch("forestadmin.agent_toolkit.utils.http.aiohttp.ClientSession", client_session_mock):
            response = self.loop.run_until_complete(
                ForestHttpApi.post("http://addr", {"body": "dict"}, {"headers": "headers"})
            )

            self.assertIsNone(response)

        mock_session.post.assert_called_once_with("http://addr", json={"body": "dict"}, headers={"headers": "headers"})

    def test_post_should_make_a_post_request_and_raise_exception_on_http_error(self):
        mock_session = Mock()
        mock_session.post = Mock(side_effect=aiohttp.ClientError("client_error"))
        mock_session.post.return_value.__aenter__ = AsyncMock()
        mock_session.post.return_value.__aexit__ = AsyncMock()

        client_session_mock = Mock()
        client_session_mock.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        client_session_mock.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch("forestadmin.agent_toolkit.utils.http.aiohttp.ClientSession", client_session_mock):
            self.assertRaisesRegex(
                ForestHttpApiException,
                r"🌳🌳🌳Failed to fetch http://addr : client_error",
                self.loop.run_until_complete,
                ForestHttpApi.post("http://addr", {"body": "dict"}, {"headers": "headers"}),
            )

        mock_session.post.assert_called_once_with("http://addr", json={"body": "dict"}, headers={"headers": "headers"})

    def test_get_should_make_a_get_request_and_return_json(self):
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"ret": True})

        mock_session = Mock()
        mock_session.get = Mock()
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.get.return_value.__aexit__ = AsyncMock()

        client_session_mock = Mock()
        client_session_mock.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        client_session_mock.return_value.__aexit__ = AsyncMock()

        with patch("forestadmin.agent_toolkit.utils.http.aiohttp.ClientSession", client_session_mock):
            response = self.loop.run_until_complete(ForestHttpApi.get("http://addr", {"headers": "headers"}))

            self.assertEqual(response, {"ret": True})

        mock_session.get.assert_called_once_with("http://addr", headers={"headers": "headers"})
        mock_response.json.assert_awaited_once()

    def test_get_should_make_a_get_request_and_return_None_if_no_200_answer(self):
        response = Mock()
        response.status = 204

        mock_session = Mock()
        mock_session.get = Mock()
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=response)
        mock_session.get.return_value.__aexit__ = AsyncMock()

        client_session_mock = Mock()
        client_session_mock.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        client_session_mock.return_value.__aexit__ = AsyncMock()

        with patch("forestadmin.agent_toolkit.utils.http.aiohttp.ClientSession", client_session_mock):
            response = self.loop.run_until_complete(ForestHttpApi.get("http://addr", {"headers": "headers"}))

            self.assertIsNone(response)
        mock_session.get.assert_called_once_with("http://addr", headers={"headers": "headers"})

    def test_get_should_make_a_get_request_and_raise_exception_on_http_error(self):
        mock_session = Mock()
        mock_session.__aexit__ = Mock()
        mock_session.get = Mock(side_effect=aiohttp.ClientError("client_error"))
        mock_session.get.return_value.__aenter__ = AsyncMock()
        mock_session.get.return_value.__aexit__ = AsyncMock()

        client_session_mock = Mock()
        client_session_mock.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        client_session_mock.return_value.__aexit__ = AsyncMock(return_value=False)
        client_session_mock.__aexit__ = AsyncMock(return_value=False)

        with patch("forestadmin.agent_toolkit.utils.http.aiohttp.ClientSession", client_session_mock):
            self.assertRaisesRegex(
                ForestHttpApiException,
                r"🌳🌳🌳Failed to fetch http://addr : client_error",
                self.loop.run_until_complete,
                ForestHttpApi.get("http://addr", {"headers": "headers"}),
            )
        mock_session.get.assert_called_once_with("http://addr", headers={"headers": "headers"})
