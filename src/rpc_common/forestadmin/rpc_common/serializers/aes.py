import base64

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


def aes_encrypt(message, aes_key: bytes, aes_iv: bytes):
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(aes_iv), backend=default_backend())
    encryptor = cipher.encryptor()

    # Pad message to 16-byte block size
    padded_message = message.ljust(16 * ((len(message) // 16) + 1), "\0")

    encrypted = encryptor.update(padded_message.encode()) + encryptor.finalize()
    return base64.b64encode(encrypted).decode()


def aes_decrypt(encrypted_message, aes_key: bytes, aes_iv: bytes):
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(aes_iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_padded = decryptor.update(base64.b64decode(encrypted_message)) + decryptor.finalize()
    return decrypted_padded.rstrip(b"\0").decode()
