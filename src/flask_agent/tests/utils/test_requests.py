from io import BytesIO
from unittest import TestCase
from unittest.mock import Mock

from flask.wrappers import Request as FlaskRequest
from flask.wrappers import Response as FlaskResponse
from forestadmin.agent_toolkit.utils.context import FileResponse, Request, Response
from forestadmin.flask_agent.utils.requests import convert_request, convert_response


class TestRequests(TestCase):
    def test_convert_request_get(self):
        flask_request_mock = Mock(FlaskRequest)
        flask_request_mock.method = "GET"
        flask_request_mock.args = {}
        flask_request_mock.view_args = {"collection_name": "customer"}
        flask_request_mock.headers = {"host": "127.0.0.1:5000", "host_url": "http://127.0.0.1:5000/"}
        request = convert_request(flask_request_mock)

        assert isinstance(request, Request)
        assert request.method.name == flask_request_mock.method
        assert request.body is None
        assert request.query == flask_request_mock.view_args
        assert request.headers == flask_request_mock.headers
        assert request.user is None

    def test_convert_request_post(self):
        flask_request_mock = Mock(FlaskResponse)
        flask_request_mock.method = "POST"
        flask_request_mock.view_args = {"collection_name": "customer"}
        flask_request_mock.args = {}
        flask_request_mock.view_args = {}
        flask_request_mock.headers = {"host": "127.0.0.1:5000", "host_url": "http://127.0.0.1:5000/"}

        flask_request_mock.get_data = Mock(return_value=b'{"renderingId":"9"}')
        flask_request_mock.json = {"renderingId": "9"}

        request = convert_request(flask_request_mock)

        assert isinstance(request, Request)
        assert request.method.name == flask_request_mock.method
        assert request.body == flask_request_mock.json
        assert request.query == flask_request_mock.view_args
        assert request.headers == flask_request_mock.headers
        assert request.user is None


class TestResponse(TestCase):
    def test_response(self):
        mocked_response = Mock(Response)
        mocked_response.body = '{"data": []}'
        mocked_response.status = 200
        mocked_response.headers = {"Content-Type": "application/json"}
        response = convert_response(mocked_response)

        assert isinstance(response, FlaskResponse)
        assert response.status_code == mocked_response.status
        assert response.status == "200 OK"
        assert response.headers["Content-Type"] == "application/json"

    def test_file_response(self):
        mocked_file_response = Mock(FileResponse)
        mocked_file_response.status = 200
        mocked_file_response.mimetype = "application/json"
        mocked_file_response.name = "test.json"
        mocked_file_response.file = BytesIO('{"data": []}'.encode("utf-8"))
        response = convert_response(mocked_file_response)

        assert isinstance(response, FlaskResponse)
        assert response.status_code == mocked_file_response.status
        assert response.status == "200 OK"
        assert response.headers["Content-Type"] == "application/json"
        assert response.content_type == "application/json"
        assert response.mimetype == "application/json"
        assert response.headers["Content-Disposition"] == "attachment; filename=test.json"
        assert response.headers["Content-Disposition"] == "attachment; filename=test.json"
        assert response.data == b'{"data": []}'
