import base64
import json
from typing import Any

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


def encrypt_response(response: dict[str, Any], aes_key: bytes, iv: bytes) -> str:
    """
    Encrypt a response dictionary using AES-GCM with a modified initialization vector (IV).

    The IV bytes are bitwise inverted, and the resulting AES-GCM ciphertext and authentication tag are concatenated
    and returned as a Base64-encoded string.

    :param response: Dictionary containing the data to be encrypted
    :param aes_key: AES encryption key in bytes
    :param iv: Initialization vector (IV) in bytes, which will be inverted before use

    :return: Base64-encoded string of the encrypted response including ciphertext and authentication tag
    """
    # Invert the IV bits
    flipped_iv = bytearray(b ^ 0xFF for b in iv)

    # Configure AES-GCM cipher with the modified IV
    encryptor = Cipher(
        algorithms.AES(aes_key),
        modes.GCM(bytes(flipped_iv)),
        backend=default_backend()
    ).encryptor()

    # Encrypt the response data and obtain the authentication tag
    ciphertext = encryptor.update(json.dumps(response).encode("utf-8")) + encryptor.finalize()
    tag = encryptor.tag

    # Concatenate ciphertext and tag, then encode in Base64
    encrypted_response = base64.b64encode(ciphertext + tag).decode("utf-8")

    return encrypted_response

def decrypt_request(
    encrypted_flow_data_b64: str, encrypted_aes_key_b64: str, initial_vector_b64: str,
    meta_private_key: str, private_key_password: str
) -> tuple[Any, bytes, bytes]:
    """
    Decrypt an encrypted request containing AES-GCM encrypted data with an RSA-encrypted AES key.

    This function uses the provided private RSA key to decrypt the AES key, then uses the AES-GCM algorithm
    to decrypt the main flow data.

    :param encrypted_flow_data_b64: Base64-encoded AES-GCM encrypted data
    :param encrypted_aes_key_b64: Base64-encoded RSA-encrypted AES key
    :param initial_vector_b64: Base64-encoded initialization vector (IV) used for AES-GCM
    :param meta_private_key: RSA private key in PEM format as a string
    :param private_key_password: Password for the RSA private key

    :return: Tuple containing the decrypted data (as a dictionary), AES key, and IV
    """
    # Decode Base64 inputs
    flow_data = base64.b64decode(encrypted_flow_data_b64)
    iv = base64.b64decode(initial_vector_b64)
    encrypted_aes_key = base64.b64decode(encrypted_aes_key_b64)

    # Load the private RSA key and decrypt the AES key
    private_key = serialization.load_pem_private_key(
        meta_private_key.encode('utf-8'),
        password=private_key_password.encode('utf-8'),
        backend=default_backend()
    )
    aes_key = private_key.decrypt(
        encrypted_aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    # Separate the encrypted flow data into ciphertext and authentication tag
    encrypted_flow_data_body = flow_data[:-16]
    encrypted_flow_data_tag = flow_data[-16:]

    # Configure AES-GCM cipher with the IV and authentication tag
    decryptor = Cipher(
        algorithms.AES(aes_key),
        modes.GCM(iv, encrypted_flow_data_tag),
        backend=default_backend()
    ).decryptor()

    # Decrypt the flow data and validate the authentication tag
    decrypted_data_bytes = decryptor.update(encrypted_flow_data_body) + decryptor.finalize()
    decrypted_data = json.loads(decrypted_data_bytes.decode("utf-8"))

    return decrypted_data, aes_key, iv
