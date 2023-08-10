from typing import Awaitable

from forestadmin.datasource_toolkit.decorators.hook.context.hooks import HookContext
from forestadmin.datasource_toolkit.decorators.hook.types import HookHandler, Position


class Hooks:
    def __init__(self) -> None:
        self.after = []
        self.before = []

    def add_handler(self, position: Position, handler: HookHandler):
        if position == "After":
            self.after.append(handler)
        elif position == "Before":
            self.before.append(handler)

    async def execute_before(self, context: HookContext):
        for hook in self.before:
            result = hook(context)
            if isinstance(result, Awaitable):
                await result

    async def execute_after(self, context: HookContext):
        for hook in self.after:
            result = hook(context)
            if isinstance(result, Awaitable):
                await result
