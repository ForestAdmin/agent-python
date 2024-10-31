import asyncio
import sys
from unittest import TestCase
from unittest.mock import AsyncMock, Mock

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.hook.context.hooks import HookContext
from forestadmin.datasource_toolkit.decorators.hook.hooks import Hooks


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
                request={"ip": "127.0.0.1"},
            ),
        )


class TestHook(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()

    def setUp(self) -> None:
        self.context = FakeHookContext()
        self.hooks = Hooks()


class TestBeforeHook(TestHook):
    def test_should_call_all_defined_hooks(self):
        first_hook = Mock()
        second_hook = AsyncMock()

        self.hooks.add_handler("Before", first_hook)
        self.hooks.add_handler("Before", second_hook)

        self.loop.run_until_complete(self.hooks.execute_before(self.context))

        first_hook.assert_called_once_with(self.context)
        second_hook.assert_awaited_once_with(self.context)

    def test_should_call_the_second_hook_with_updated_context(self):
        def first_hook_fn(context):
            context.a_prop = 1

        first_hook = Mock(side_effect=first_hook_fn)

        async def second_hook_fn(context):
            self.assertEqual(context.a_prop, 1)

        second_hook = AsyncMock(side_effect=second_hook_fn)

        self.hooks.add_handler("Before", first_hook)
        self.hooks.add_handler("Before", second_hook)

        self.loop.run_until_complete(self.hooks.execute_before(self.context))

        first_hook.assert_called_once_with(self.context)
        second_hook.assert_awaited_once_with(self.context)

    def test_should_not_execute_second_hook_if_first_on_raise(self):
        first_hook = Mock(side_effect=Exception)
        second_hook = AsyncMock()

        self.hooks.add_handler("Before", first_hook)
        self.hooks.add_handler("Before", second_hook)

        self.assertRaises(Exception, self.loop.run_until_complete, self.hooks.execute_before(self.context))

        first_hook.assert_called_once_with(self.context)
        second_hook.assert_not_awaited()

    def test_should_not_call_after_hook_on_before(self):
        before_handler = Mock()
        self.hooks.add_handler("After", before_handler)

        self.loop.run_until_complete(self.hooks.execute_before(self.context))
        before_handler.assert_not_called()


class TestAfterHook(TestHook):
    def test_should_call_all_defined_hooks(self):
        first_hook = Mock()
        second_hook = AsyncMock()

        self.hooks.add_handler("After", first_hook)
        self.hooks.add_handler("After", second_hook)

        self.loop.run_until_complete(self.hooks.execute_after(self.context))

        first_hook.assert_called_once_with(self.context)
        second_hook.assert_awaited_once_with(self.context)

    def test_should_call_the_second_hook_with_updated_context(self):
        def first_hook_fn(context):
            context.a_prop = 1

        first_hook = Mock(side_effect=first_hook_fn)

        async def second_hook_fn(context):
            self.assertEqual(context.a_prop, 1)

        second_hook = AsyncMock(side_effect=second_hook_fn)

        self.hooks.add_handler("After", first_hook)
        self.hooks.add_handler("After", second_hook)

        self.loop.run_until_complete(self.hooks.execute_after(self.context))

        first_hook.assert_called_once_with(self.context)
        second_hook.assert_awaited_once_with(self.context)

    def test_should_not_execute_second_hook_if_first_on_raise(self):
        first_hook = Mock(side_effect=Exception)
        second_hook = AsyncMock()

        self.hooks.add_handler("After", first_hook)
        self.hooks.add_handler("After", second_hook)

        self.assertRaises(Exception, self.loop.run_until_complete, self.hooks.execute_after(self.context))

        first_hook.assert_called_once_with(self.context)
        second_hook.assert_not_awaited()

    def test_should_not_call_before_hook_on_after(self):
        before_handler = Mock()
        self.hooks.add_handler("Before", before_handler)

        self.loop.run_until_complete(self.hooks.execute_after(self.context))
        before_handler.assert_not_called()
