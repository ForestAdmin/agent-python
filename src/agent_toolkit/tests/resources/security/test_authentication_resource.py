import asyncio
import json
from unittest import TestCase
from unittest.mock import AsyncMock, Mock, patch

from forestadmin.agent_toolkit.resources.security.exceptions import AuthenticationException, OpenIdException
from forestadmin.agent_toolkit.resources.security.resources import Authentication
from forestadmin.agent_toolkit.services.permissions.ip_whitelist_service import IpWhiteListService
from forestadmin.agent_toolkit.utils.authentication import CustomClientOic
from forestadmin.agent_toolkit.utils.context import Request, RequestMethod
from forestadmin.agent_toolkit.utils.token import build_jwt


class TestAuthenticationResource(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()
        cls.options = {"auth_secret": "auth secret"}
        cls.ip_white_list_mock = Mock(IpWhiteListService)
        cls.ip_white_list_mock.is_enable = AsyncMock(return_value=False)

    def setUp(self) -> None:
        self.authentication_resource = Authentication(self.ip_white_list_mock, self.options)


class TestAuthenticationResourceDispatch(TestAuthenticationResource):
    def test_dispatch_should_call_the_authenticate(self):
        request = Request(RequestMethod.GET)
        with patch.object(self.authentication_resource, "authenticate", new_callable=AsyncMock) as mocked_authenticate:
            self.loop.run_until_complete(self.authentication_resource.dispatch(request, "authenticate"))
            mocked_authenticate.assert_awaited_once_with(request)

    def test_dispatch_should_call_the_callback_method(self):
        request = Request(RequestMethod.GET)
        with patch.object(self.authentication_resource, "callback", new_callable=AsyncMock) as mocked_callback:
            self.loop.run_until_complete(self.authentication_resource.dispatch(request, "callback"))
            mocked_callback.assert_awaited_once_with(request)

    def test_dispatch_should_call_handle_error_on_error_on_authenticate(self):
        request = Request(RequestMethod.GET)
        exception = AuthenticationException("an error is needed")
        with patch.object(
            self.authentication_resource,
            "authenticate",
            new_callable=AsyncMock,
            side_effect=exception,
        ):
            with patch.object(self.authentication_resource, "_handle_error") as mocked_handle_error:
                self.loop.run_until_complete(self.authentication_resource.dispatch(request, "authenticate"))
            mocked_handle_error.assert_called_once_with("authenticate", request, exception)

    def test_dispatch_should_call_handle_error_on_error_on_callback(self):
        request = Request(RequestMethod.GET)
        exception = AuthenticationException("an error is needed")
        with patch.object(
            self.authentication_resource,
            "callback",
            new_callable=AsyncMock,
            side_effect=exception,
        ):
            with patch.object(self.authentication_resource, "_handle_error") as mocked_handle_error:
                self.loop.run_until_complete(self.authentication_resource.dispatch(request, "callback"))
            mocked_handle_error.assert_called_once_with("callback", request, exception)


class TestAuthenticationResourceAuthenticate(TestAuthenticationResource):
    def test_authenticate_should_raise_when_no_body_in_request(self):
        request = Request(RequestMethod.POST, body={})

        self.assertRaisesRegex(
            AuthenticationException,
            r"^...renderingId is missing in the request's body$",
            self.loop.run_until_complete,
            self.authentication_resource.authenticate(request),
        )

    def test_authenticate_should_raise_when_rendering_id_not_in_request_body(self):
        request = Request(RequestMethod.POST, body={"notRenderingId": None})

        self.assertRaisesRegex(
            AuthenticationException,
            r"^...renderingId is missing in the request's body$",
            self.loop.run_until_complete,
            self.authentication_resource.authenticate(request),
        )

    def test_authenticate_should_raise_when_rendering_id_is_not_parsable_as_an_integer(self):
        request = Request(RequestMethod.POST, body={"renderingId": "not_integer"})

        self.assertRaisesRegex(
            AuthenticationException,
            r"^...renderingId should be an integer$",
            self.loop.run_until_complete,
            self.authentication_resource.authenticate(request),
        )

    def test_authenticate_should_create_oic_client_with_options_and_get_authorization_url(self):
        custom_client = Mock(CustomClientOic)
        custom_client.get_authorization_url = Mock(return_value="http://my.authorization.url/")

        request = Request(RequestMethod.POST, body={"renderingId": "12"})
        with patch(
            "forestadmin.agent_toolkit.resources.security.resources.ClientFactory.build",
            new_callable=AsyncMock,
            return_value=custom_client,
        ) as mocked_client_factory_build:
            response = self.loop.run_until_complete(self.authentication_resource.authenticate(request))
            mocked_client_factory_build.assert_awaited_once_with(self.options)
            custom_client.get_authorization_url.assert_called_once_with('{"renderingId": 12}')

        self.assertEqual(response.status, 200)
        self.assertEqual(response.headers, {"content_type": "application/json"})
        self.assertEqual(response.body, '{"authorizationUrl": "http://my.authorization.url/"}')


class TestAuthenticationResourceCallback(TestAuthenticationResource):
    def test_callback_should_raise_when_no_query_params(self):
        request = Request(RequestMethod.GET, query=None)
        with patch(
            "forestadmin.agent_toolkit.resources.security.resources.ClientFactory.build",
            new_callable=AsyncMock,
        ) as mocked_client_factory_build:
            self.assertRaisesRegex(
                AuthenticationException,
                r"^...`state`should be sent to the callback endpoint$",
                self.loop.run_until_complete,
                self.authentication_resource.callback(request),
            )
            mocked_client_factory_build.assert_awaited_once_with(self.options)

    def test_callback_should_raise_when_state_query_params_is_not_set(self):
        request = Request(RequestMethod.GET, query={"notState": None})
        with patch(
            "forestadmin.agent_toolkit.resources.security.resources.ClientFactory.build",
            new_callable=AsyncMock,
        ):
            self.assertRaisesRegex(
                AuthenticationException,
                r"^...`state`should be sent to the callback endpoint$",
                self.loop.run_until_complete,
                self.authentication_resource.callback(request),
            )

    def test_callback_should_raise_when_state_query_params_is_not_json_parsable(self):
        request = Request(RequestMethod.GET, query={"state": 'not{json"renderingId":"12"}'})
        with patch(
            "forestadmin.agent_toolkit.resources.security.resources.ClientFactory.build",
            new_callable=AsyncMock,
        ):
            self.assertRaisesRegex(
                AuthenticationException,
                r"^...state should be a json$",
                self.loop.run_until_complete,
                self.authentication_resource.callback(request),
            )

    def test_callback_should_raise_when_rendering_id_not_in_state(self):
        request = Request(RequestMethod.GET, query={"state": '{"notRenderingId":"12"}'})
        with patch(
            "forestadmin.agent_toolkit.resources.security.resources.ClientFactory.build",
            new_callable=AsyncMock,
        ):
            self.assertRaisesRegex(
                AuthenticationException,
                r"^...renderingId is missing in the callback state$",
                self.loop.run_until_complete,
                self.authentication_resource.callback(request),
            )

    def test_callback_should_raise_when_rendering_id_not_parsable_as_int(self):
        request = Request(RequestMethod.GET, query={"state": '{"renderingId":"aa12"}'})
        with patch(
            "forestadmin.agent_toolkit.resources.security.resources.ClientFactory.build",
            new_callable=AsyncMock,
        ):
            self.assertRaisesRegex(
                AuthenticationException,
                r"^...renderingId should be an integer$",
                self.loop.run_until_complete,
                self.authentication_resource.callback(request),
            )

    def test_callback_should_query_backend_for_rendering_permissions(self):
        custom_client = Mock(CustomClientOic)
        custom_client.get_parsed_response = Mock(return_value="parsed_response")
        custom_client.get_access_token = Mock(return_value={"access_token": "token"})
        user = {
            "email": "foo.bar@email.com",
            "first_name": "foo",
            "last_name": "bar",
            "teams": ["bestTeam"],
        }

        request = Request(RequestMethod.GET, query={"state": '{"renderingId":"12"}'})
        with patch(
            "forestadmin.agent_toolkit.resources.security.resources.ClientFactory.build",
            new_callable=AsyncMock,
            return_value=custom_client,
        ):
            with patch(
                "forestadmin.agent_toolkit.resources.security.resources.ForestHttpApi.get_rendering_authorization",
                new_callable=AsyncMock,
                return_value={"data": {"id": 12, "attributes": user}},
            ) as mock_http_get_rendering_permissions:
                self.loop.run_until_complete(self.authentication_resource.callback(request))
                mock_http_get_rendering_permissions.assert_awaited_once_with(12, "token", self.options)

    def test_callback_should_return_http_response_with_jwt(self):
        custom_client = Mock(CustomClientOic)
        custom_client.get_parsed_response = Mock(return_value="parsed_response")
        custom_client.get_access_token = Mock(return_value={"access_token": "token"})
        user = {
            "email": "foo.bar@email.com",
            "first_name": "foo",
            "last_name": "bar",
            "teams": ["bestTeam"],
        }

        request = Request(RequestMethod.GET, query={"state": '{"renderingId":"12"}'})
        with patch(
            "forestadmin.agent_toolkit.resources.security.resources.ClientFactory.build",
            new_callable=AsyncMock,
            return_value=custom_client,
        ):
            with patch(
                "forestadmin.agent_toolkit.resources.security.resources.ForestHttpApi.get_rendering_authorization",
                new_callable=AsyncMock,
                return_value={"data": {"id": 12, "attributes": user}},
            ):
                response = self.loop.run_until_complete(self.authentication_resource.callback(request))

            custom_client.get_parsed_response.assert_called_once_with(request.query)
            custom_client.get_access_token.assert_called_once_with("parsed_response")

        self.assertEqual(response.status, 200)
        self.assertEqual(response.headers, {"content_type": "application/json"})
        token, body = build_jwt(
            {
                "id": 12,
                "email": user["email"],
                "first_name": user["first_name"],
                "last_name": user["last_name"],
                "team": user["teams"][0],
                "rendering_id": 12,
            },
            self.options["auth_secret"],
        )
        body_content = json.loads(response.body)
        body_content["tokenData"].pop("exp")
        body.pop("exp")
        self.assertEqual(body_content["tokenData"], body)


class TestAuthenticationResourceHandleError(TestAuthenticationResource):
    def test_handle_error_should_return_http_response_401_for_authentication_errors(self):
        request = Request(RequestMethod.GET)
        response = self.authentication_resource._handle_error(
            "authenticate", request, AuthenticationException("state should be a json")
        )

        self.assertEqual(response.status, 401)

    def test_handle_error_should_return_http_response_401_with_openid_error_for_opend_id_exceptions(self):
        request = Request(RequestMethod.GET)
        response = self.authentication_resource._handle_error(
            "authenticate",
            request,
            OpenIdException("error given in the query GET params", "error", "error_description", "state"),
        )

        self.assertEqual(response.status, 401)
        response_content = json.loads(response.body)
        self.assertEqual(response_content["error"], "error")
        self.assertEqual(response_content["error_description"], "error_description")
        self.assertEqual(response_content["state"], "state")

    def test_handle_error_should_re_throw_errors_unrelated_to_authentication(self):
        request = Request(RequestMethod.GET)

        self.assertRaisesRegex(
            Exception,
            r"re raise me",
            self.authentication_resource._handle_error,
            "authenticate",
            request,
            Exception("re raise me"),
        )
