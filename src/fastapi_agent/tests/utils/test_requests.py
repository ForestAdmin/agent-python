import asyncio
from io import BytesIO
from unittest import TestCase
from unittest.mock import AsyncMock, Mock

from fastapi import Request as FastAPIRequest
from fastapi import Response as FastAPIResponse
from forestadmin.agent_toolkit.utils.context import FileResponse, Request, Response
from forestadmin.fastapi_agent.utils.requests import convert_request, convert_response


class TestRequests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()

    def test_convert_request_get(self):
        flask_request_mock = Mock(FastAPIRequest)
        flask_request_mock.method = "GET"
        flask_request_mock.query_params = {}
        flask_request_mock.path_params = {"collection_name": "customer"}
        flask_request_mock.headers = {"host": "127.0.0.1:5000", "host_url": "http://127.0.0.1:5000/"}
        flask_request_mock.client = Mock()
        flask_request_mock.client.host = "127.0.0.1"
        request = self.loop.run_until_complete(convert_request(flask_request_mock))

        self.assertTrue(isinstance(request, Request))
        self.assertEqual(request.method.name, flask_request_mock.method)
        self.assertEqual(request.body, None)
        self.assertEqual(request.query, flask_request_mock.path_params)
        self.assertEqual(request.headers, {"Host": "127.0.0.1:5000", "Host_Url": "http://127.0.0.1:5000/"})
        self.assertEqual(request.user, None)
        self.assertEqual(request.client_ip, "127.0.0.1")

    def test_convert_request_post(self):
        flask_request_mock = Mock(FastAPIResponse)
        flask_request_mock.method = "POST"
        flask_request_mock.path_params = {"collection_name": "customer"}
        flask_request_mock.query_params = {}
        flask_request_mock.path_params = {}
        flask_request_mock.headers = {"host": "127.0.0.1:5000", "host_url": "http://127.0.0.1:5000/"}
        flask_request_mock.client = Mock()
        flask_request_mock.client.host = "127.0.0.1"

        flask_request_mock.body = AsyncMock(return_value=b'{"renderingId":"9"}')
        flask_request_mock.json = AsyncMock(return_value={"renderingId": "9"})

        request = self.loop.run_until_complete(convert_request(flask_request_mock))

        self.assertTrue(isinstance(request, Request))
        self.assertEqual(request.method.name, flask_request_mock.method)
        self.assertEqual(request.body, {"renderingId": "9"})
        self.assertEqual(request.query, flask_request_mock.path_params)
        self.assertEqual(request.headers, {"Host": "127.0.0.1:5000", "Host_Url": "http://127.0.0.1:5000/"})
        self.assertEqual(request.user, None)
        self.assertEqual(request.client_ip, "127.0.0.1")

    def test_client_ip_must_be_the_forwarded_one(self):
        flask_request_mock = Mock(FastAPIRequest)
        flask_request_mock.method = "GET"
        flask_request_mock.query_params = {}
        flask_request_mock.path_params = {"collection_name": "customer"}
        flask_request_mock.headers = {
            "host": "127.0.0.1:5000",
            "host_url": "http://127.0.0.1:5000/",
            "x-forwarded-for": "192.168.1.10",
        }
        flask_request_mock.client = Mock()
        flask_request_mock.client.host = "127.0.0.1"
        request = self.loop.run_until_complete(convert_request(flask_request_mock))

        self.assertNotEqual(request.client_ip, flask_request_mock.client.host)
        self.assertEqual(request.client_ip, "192.168.1.10")


class TestResponse(TestCase):
    def test_response(self):
        mocked_response = Mock(Response)
        mocked_response.body = '{"data": []}'
        mocked_response.status = 200
        mocked_response.headers = {"Content-Type": "application/json"}
        fastapi_response = convert_response(mocked_response)

        self.assertTrue(isinstance(fastapi_response, FastAPIResponse))
        self.assertEqual(fastapi_response.status_code, mocked_response.status)
        self.assertEqual(fastapi_response.headers["Content-Type"], "application/json")
        self.assertEqual(fastapi_response.body, mocked_response.body.encode("utf-8"))

    def test_file_response(self):
        mocked_file_response = Mock(FileResponse)
        mocked_file_response.status = 200
        mocked_file_response.mimetype = "application/json"
        mocked_file_response.name = "test.json"
        mocked_file_response.file = BytesIO('{"data": []}'.encode("utf-8"))
        mocked_file_response.headers = {"custom-header": "custom-value"}
        response = convert_response(mocked_file_response)

        self.assertTrue(isinstance(response, FastAPIResponse))
        self.assertEqual(response.status_code, mocked_file_response.status)
        self.assertEqual(response.headers["custom-header"], "custom-value")
        self.assertEqual(response.headers["content-type"], "application/json")
        self.assertEqual(response.headers["content-disposition"], 'attachment; filename="test.json"')
        self.assertEqual(response.body, b'{"data": []}')
