from typing_extensions import TypedDict


class RpcOptions(TypedDict):
    listen_addr: str
    aes_key: bytes
    aes_iv: bytes
