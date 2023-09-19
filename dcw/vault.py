from cryptography.fernet import Fernet
from hashlib import sha256
from base64 import b64encode


def encrypt_file(content: str, output_file_path: str, crypt_key: str):
    key_hash = b64encode(sha256(crypt_key.encode('utf-8')).digest())
    frn = Fernet(key_hash)
    encrypted_content = frn.encrypt(content.encode('utf-8'))
    with open(output_file_path, 'wb') as f:
        f.write(encrypted_content)


def decrypt_file(file_path: str, crypt_key: str):
    key_hash = b64encode(sha256(crypt_key.encode('utf-8')).digest())
    frn = Fernet(key_hash)
    with open(file_path, 'rb') as f:
        return frn.decrypt(f.read())


class DCWVaultConfig:
    def __init__(self) -> None:
        self.environments = []


def read_valut_config_from_file():
    pass
