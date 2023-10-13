def bytes2hex(data: bytes) -> str:
    return "".join([f"{c:X}" for c in data])
    # return "".join([f"{ord(c):X}" for c in data])


def hex2bytes(data: str) -> bytes:
    ret = ""
    for i in range(0, len(data), 2):
        ret += chr(int(data[i : i + 2], 16))
    return ret.encode("ascii")
