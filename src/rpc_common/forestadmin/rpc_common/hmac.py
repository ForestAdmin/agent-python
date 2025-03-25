import hashlib
import hmac


def generate_hmac(key: bytes, message: bytes) -> str:
    return hmac.new(key, message, hashlib.sha256).hexdigest()


def is_valid_hmac(key: bytes, message: bytes, sign: bytes) -> bool:
    expected_hmac = generate_hmac(key, message).encode("utf-8")
    return hmac.compare_digest(expected_hmac, sign)
