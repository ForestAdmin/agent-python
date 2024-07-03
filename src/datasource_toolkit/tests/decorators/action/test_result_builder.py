from io import BytesIO, StringIO
from unittest import TestCase

from forestadmin.datasource_toolkit.decorators.action.result_builder import ResultBuilder


class TestActionResultBuilder(TestCase):
    def test_success_should_work_without_argument(self):
        result = ResultBuilder().success()
        assert result == {
            "type": "Success",
            "message": "Success",
            "format": "text",
            "invalidated": set(),
            "response_headers": {},
        }

    def test_success_should_work_with_message_and_option(self):
        result = ResultBuilder().success("<h1>It works !</h1>", {"type": "html"})

        assert result == {
            "type": "Success",
            "message": "<h1>It works !</h1>",
            "format": "html",
            "invalidated": set(),
            "response_headers": {},
        }

    def test_error_should_work_without_argument(self):
        result = ResultBuilder().error()
        assert result == {
            "type": "Error",
            "message": "Error",
            "format": "text",
            "response_headers": {},
        }

    def test_error_should_work_with_message_and_option(self):
        result = ResultBuilder().error("<h1>It don't works !</h1>", {"type": "html"})

        assert result == {
            "type": "Error",
            "message": "<h1>It don't works !</h1>",
            "format": "html",
            "response_headers": {},
        }

    def test_webhook_should_work_without_argument(self):
        result = ResultBuilder().webhook("test.com")
        assert result == {
            "type": "Webhook",
            "url": "test.com",
            "method": "POST",
            "headers": {},
            "body": {},
            "response_headers": {},
        }

    def test_webhook_should_work_with_message_and_option(self):
        result = ResultBuilder().webhook("test.com", "PATCH", {"content-type": "application/json"}, {"key": "value"})

        assert result == {
            "type": "Webhook",
            "url": "test.com",
            "method": "PATCH",
            "headers": {"content-type": "application/json"},
            "body": {"key": "value"},
            "response_headers": {},
        }

    def test_file_should_work_with_stringIO(self):
        result = ResultBuilder().file(StringIO("id,name,email"), "test.csv", "text/csv")

        stream = result.pop("stream")
        assert stream.read() == "id,name,email"
        assert result == {
            "type": "File",
            "name": "test.csv",
            "mimeType": "text/csv",
            # "stream": StringIO("id,name,email"),
            "response_headers": {},
        }

    def test_file_should_work_with_BytesIO(self):
        result = ResultBuilder().file(BytesIO(b"id,name,email"), "test.csv", "text/csv")
        stream = result.pop("stream")

        assert stream.read() == b"id,name,email"
        assert result == {
            "type": "File",
            "name": "test.csv",
            "mimeType": "text/csv",
            # "stream": BytesIO(b"id,name,email"),
            "response_headers": {},
        }

    def test_file_should_work_with_bytes(self):
        result = ResultBuilder().file(b"id,name,email", "test.csv", "text/csv")
        stream = result.pop("stream")

        assert stream.read() == b"id,name,email"
        assert result == {
            "type": "File",
            "name": "test.csv",
            "mimeType": "text/csv",
            # "stream": BytesIO(b"id,name,email"),
            "response_headers": {},
        }

    def test_file_should_work_with_str(self):
        result = ResultBuilder().file("id,name,email", "test.csv", "text/csv")
        stream = result.pop("stream")

        assert stream.read() == "id,name,email"
        assert result == {
            "type": "File",
            "name": "test.csv",
            "mimeType": "text/csv",
            # "stream": BytesIO(b"id,name,email"),
            "response_headers": {},
        }

    def test_redirect_should_work(self):
        result = ResultBuilder().redirect("test.com")
        assert result == {
            "type": "Redirect",
            "path": "test.com",
            "response_headers": {},
        }
