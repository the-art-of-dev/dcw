from cryptography.fernet import Fernet
from hashlib import sha256
from base64 import b64encode
import yaml


def encrypt_file(content: str, output_file_path: str, crypt_key: str):
    key_hash = b64encode(sha256(crypt_key.encode('utf-8')).digest())
    frn = Fernet(key_hash)
    encrypted_content = frn.encrypt(content.encode('utf-8'))
    with open(output_file_path, 'wb') as f:
        f.write(encrypted_content)


def decrypt_file(file_path: str, crypt_key: str) -> str:
    key_hash = b64encode(sha256(crypt_key.encode('utf-8')).digest())
    frn = Fernet(key_hash)
    with open(file_path, 'rb') as f:
        return frn.decrypt(f.read()).decode('utf-8')


class DCWVaultConfig:
    def __init__(self) -> None:
        self.environments = []
        self.units = []

def read_valut_config_from_file() -> DCWVaultConfig:
    file_path = "hacking/.dcwrc.yaml"
    try:
        with open(file_path, "r") as file: 
            yaml_data = yaml.load(file, Loader=yaml.FullLoader)
    except FileNotFoundError:
        print(f"The file {file_path} does not exist.")
    DCWVaultConfig.environments = yaml_data['vault']['environments']
    
    return DCWVaultConfig