from forestadmin.datasource_toolkit.decorators.hook.context.hooks import HookContext
from forestadmin.datasource_toolkit.decorators.hook.types import HookHandler, Position
from forestadmin.datasource_toolkit.utils.user_callable import call_user_function


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
            await call_user_function(hook, context)

    async def execute_after(self, context: HookContext):
        for hook in self.after:
            await call_user_function(hook, context)
