import asyncio
import json
from unittest import TestCase
from unittest.mock import AsyncMock, Mock, patch

from forestadmin.agent_toolkit.resources.security.exceptions import OpenIdException
from forestadmin.agent_toolkit.utils.authentication import ClientFactory, CustomClientOic
from oic.oic.message import AuthorizationResponse


class TestCustomClientOic(TestCase):
    def test_register_should_call_http_url_with_env_secret(self):
        mock_response = Mock()
        client = CustomClientOic()
        client.events = Mock()
        body_data = json.dumps(
            {"application_type": "web", "response_types": ["code"], "grant_types": ["authorization_code"]}
        )
        with patch.object(client, "http_request", return_value=mock_response) as mocked_http_request:
            with patch.object(
                client, "handle_registration_info", side_effect=lambda rsp: rsp
            ) as mocked_handle_registration:
                response = client.register("https://api.development.forestadmin.com/oidc/reg", "env_secret")

                mocked_http_request.assert_called_once_with(
                    "https://api.development.forestadmin.com/oidc/reg",
                    "POST",
                    data=body_data,
                    headers={"content-type": "application/json", "Authorization": "Bearer env_secret"},
                )
                mocked_handle_registration.assert_called_once_with(response)

    def test_get_authorization_url_should_return_the_correct_url(self):
        client = CustomClientOic()
        client.registration_response = {"redirect_uris": ["https://my_project.com/forest/authentication/callback"]}
        client.authorization_endpoint = "https://api.development.forestadmin.com/oidc/auth"
        ret = client.get_authorization_url('{"renderingId": 12}')
        self.assertEqual(
            ret,
            "https://api.development.forestadmin.com/oidc/auth?response_type=code&scope=openid+email+profile&state=%7B"
            "%22renderingId%22%3A+12%7D&redirect_uri=https%3A%2F%2Fmy_project.com%2Fforest%2Fauthentication%2Fcallback",
        )

    def test_get_parsed_response_should_raise_if_there_is_an_error_in_param(self):
        params = {"error": "my_error", "error_description": "my error_description", "state": '{"renderingId": 28}'}
        client = CustomClientOic()
        self.assertRaisesRegex(
            OpenIdException,
            r"error given in the query GET params",
            client.get_parsed_response,
            params,
        )
        try:
            client.get_parsed_response(params)
        except OpenIdException as exc:
            self.assertEqual(exc.error, "my_error")
            self.assertEqual(exc.error_description, "my error_description")
            self.assertEqual(exc.state, '{"renderingId": 28}')

    def test_get_parsed_response_should_proxy_call_parse_response(self):
        params = {"code": "secret_token", "state": '{"renderingId": 28}'}
        client = CustomClientOic()
        with patch.object(client, "parse_response", return_value="return") as mock_parse_response:
            client.get_parsed_response(params)
            mock_parse_response.assert_called_once_with(
                AuthorizationResponse,
                info='{"code": "secret_token", "state": "{\\"renderingId\\": 28}"}',
                state='{"renderingId": 28}',
                scope=["openid", "email", "profile"],
            )

    def test_get_access_token_should_call_do_access_token_and_return_it(self):
        client = CustomClientOic()
        with patch.object(client, "do_access_token_request", return_value="access_token") as mock_do_AT:
            access_token = client.get_access_token({"state": '{"renderingId": 28}', "code": "secret_code"})
            self.assertEqual(access_token, "access_token")
            mock_do_AT.assert_called_once_with(
                state='{"renderingId": 28}',
                request_args={"code": "secret_code"},
                verify=False,
                skew=5,
                authn_method="",
            )


class TestClientFactory(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()
        cls.options = {"auth_secret": "auth secret", "env_secret": "env_secret"}

    def test_build_should_return_client_if_already_created(self):
        with patch("forestadmin.agent_toolkit.utils.authentication.ClientFactory.oic_client", "oic_client"):
            client = self.loop.run_until_complete(ClientFactory.build(self.options))
            self.assertEqual(client, "oic_client")

    def test_build_should_create_a_ready_to_use_custom_oic_client(self):
        issuer_metadata_mock = {
            "issuer": "https://api.development.forestadmin.com",
            "registration_endpoint": "https://api.development.forestadmin.com/oidc/reg",
        }

        with patch(
            "forestadmin.agent_toolkit.utils.authentication.ForestHttpApi.get_open_id_issuer_metadata",
            new_callable=AsyncMock,
            return_value=issuer_metadata_mock,
        ) as mock_http_call:
            with patch("forestadmin.agent_toolkit.utils.authentication.CustomClientOic.register") as mock_oic_register:
                client = self.loop.run_until_complete(ClientFactory.build(self.options))
                self.assertIsNotNone(client)

                mock_http_call.assert_awaited_once_with(self.options)
                mock_oic_register.assert_called_once_with(
                    "https://api.development.forestadmin.com/oidc/reg", registration_token="env_secret"
                )
                self.assertEqual(ClientFactory.oic_client, client)
                ClientFactory.oic_client = None
