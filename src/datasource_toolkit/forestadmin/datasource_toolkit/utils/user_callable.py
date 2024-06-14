from asyncio import iscoroutinefunction

try:
    from asgiref.sync import sync_to_async
except ModuleNotFoundError:
    sync_to_async = None


async def call_user_function(method, *args, **kwargs):
    if iscoroutinefunction(method):
        return await method(*args, **kwargs)
    else:
        if sync_to_async is not None:
            return await sync_to_async(method)(*args, **kwargs)
        else:
            return method(*args, **kwargs)
