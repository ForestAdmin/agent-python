from typing_extensions import TypedDict


class RpcOptions(TypedDict):
    listen_addr: str
    auth_secret: str
