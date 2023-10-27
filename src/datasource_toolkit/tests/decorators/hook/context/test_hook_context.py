import sys
from unittest import TestCase

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.hook.context.hooks import HookContext
from forestadmin.datasource_toolkit.exceptions import ForbiddenError, UnprocessableError, ValidationError


class FakeHookContext(HookContext):
    def __init__(self):
        datasource: Datasource = Datasource()

        Collection.__abstractmethods__ = set()  # to instantiate abstract class
        collection = Collection("Book", datasource)
        super().__init__(
            collection,
            User(
                rendering_id=1,
                user_id=1,
                tags={},
                email="dummy@user.fr",
                first_name="dummy",
                last_name="user",
                team="operational",
                timezone=zoneinfo.ZoneInfo("Europe/Paris"),
            ),
        )


class TestHookContext(TestCase):
    def setUp(self) -> None:
        self.context = FakeHookContext()

    def test_throw_error_should_throw_unprocessable_error(self):
        message = "unprocessableError"
        self.assertRaisesRegex(UnprocessableError, "🌳🌳🌳" + message, self.context.throw_error, message)

    def test_throw_forbidden_error_should_throw_forbidden_error(self):
        message = "forbidden"
        self.assertRaisesRegex(ForbiddenError, "🌳🌳🌳" + message, self.context.throw_forbidden_error, message)

    def test_throw_validation_error_should_throw_validation_error(self):
        message = "validation"
        self.assertRaisesRegex(ValidationError, "🌳🌳🌳" + message, self.context.throw_validation_error, message)
