import json
from unittest import TestCase

from forestadmin.agent_toolkit.utils.context import HttpResponseBuilder
from forestadmin.datasource_toolkit.exceptions import ForestException, ValidationError


class TestHttpResponseBuilder(TestCase):
    def test_build_json_response(self):
        response = HttpResponseBuilder.build_json_response(200, {"result": "test_result"})

        self.assertEqual(response.status, 200)
        self.assertEqual(response.headers, {"content-type": "application/json"})
        content = json.loads(response.body)
        self.assertEqual(content, {"result": "test_result"})

    def test_build_client_error_response(self):
        response = HttpResponseBuilder.build_client_error_response(
            [
                Exception("test exc"),
                ValidationError("test exc"),
            ]
        )

        self.assertEqual(response.status, 500)
        self.assertEqual(response.headers, {"content-type": "application/json"})
        content = json.loads(response.body)
        self.assertEqual(
            content,
            {
                "errors": [
                    {
                        "name": "Exception",
                        "detail": "test exc",
                        "status": 500,
                    },
                    {
                        "name": "ValidationError",
                        "detail": "test exc",
                        "status": 400,
                    },
                ]
            },
        )

    def test_build_client_error_response_custom_error_customizer(self):
        HttpResponseBuilder.setup_error_message_customizer(lambda error: error.args[0][3:])
        response = HttpResponseBuilder.build_client_error_response(
            [
                ForestException("test exc"),
                ValidationError("test exc"),
            ]
        )

        self.assertEqual(response.status, 500)
        self.assertEqual(response.headers, {"content-type": "application/json"})
        content = json.loads(response.body)
        self.assertEqual(
            content,
            {
                "errors": [
                    {
                        "name": "ForestException",
                        "detail": "test exc",
                        "status": 500,
                    },
                    {
                        "name": "ValidationError",
                        "detail": "test exc",
                        "status": 400,
                    },
                ]
            },
        )
        HttpResponseBuilder.setup_error_message_customizer(None)

    def test_build_client_csv(self):
        response = HttpResponseBuilder.build_csv_response("test;test", "filename.csv")

        self.assertEqual(response.status, 200)
        self.assertEqual(
            response.headers,
            {"content-type": "text/csv", "Content-Disposition": 'attachment; filename="filename.csv"'},
        )
        self.assertEqual(response.body, "test;test")

    def test_build_success(self):
        response = HttpResponseBuilder.build_success_response({"test": "test"})

        self.assertEqual(response.status, 200)
        self.assertEqual(response.headers, {"content-type": "application/json"})
        content = json.loads(response.body)
        self.assertEqual(content, {"test": "test"})

    def test_build_unknown(self):
        response = HttpResponseBuilder.build_unknown_response()

        self.assertEqual(response.status, 404)
        self.assertEqual(response.headers, {})
        self.assertEqual(response.body, None)

    def test_build_no_content(self):
        response = HttpResponseBuilder.build_no_content_response()

        self.assertEqual(response.status, 204)
        self.assertEqual(response.headers, {})
        self.assertEqual(response.body, None)

    def test_build_method_not_allowed(self):
        response = HttpResponseBuilder.build_method_not_allowed_response()

        self.assertEqual(response.status, 405)
        self.assertEqual(response.headers, {})
        self.assertEqual(response.body, None)

    def test_setup_error_message_customizer(self):
        def custom_fn(error):
            return ""

        HttpResponseBuilder.setup_error_message_customizer(custom_fn)
        self.assertEqual(HttpResponseBuilder._ERROR_MESSAGE_CUSTOMIZER, custom_fn)

        HttpResponseBuilder.setup_error_message_customizer(None)
        self.assertEqual(HttpResponseBuilder._ERROR_MESSAGE_CUSTOMIZER, None)
