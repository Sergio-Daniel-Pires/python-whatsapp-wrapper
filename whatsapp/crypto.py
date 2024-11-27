import base64
import hashlib
import hmac
import json
from typing import Any

import httpx
from Crypto.PublicKey import RSA
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7


def encrypt_response (response: dict[str, Any], aes_key: bytes, iv: bytes) -> str:
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
    encryptor = Cipher(algorithms.AES(aes_key), modes.GCM(bytes(flipped_iv))).encryptor()

    # Encrypt the response data and obtain the authentication tag
    ciphertext = encryptor.update(json.dumps(response).encode("utf-8")) + encryptor.finalize()

    # Concatenate ciphertext and tag, then encode in Base64
    encrypted_response = base64.b64encode(ciphertext + encryptor.tag).decode("utf-8")

    return encrypted_response

def decrypt_request (
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
        meta_private_key.encode("utf-8"), password=private_key_password.encode("utf-8")
    )
    aes_key = private_key.decrypt(
        encrypted_aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None
        )
    )

    # Separate the encrypted flow data into ciphertext and authentication tag
    encrypted_flow_data_body = flow_data[:-16]
    encrypted_flow_data_tag = flow_data[-16:]

    # Configure AES-GCM cipher with the IV and authentication tag
    decryptor = Cipher(
        algorithms.AES(aes_key), modes.GCM(iv, encrypted_flow_data_tag)
    ).decryptor()

    # Decrypt the flow data and validate the authentication tag
    decrypted_data_bytes = decryptor.update(encrypted_flow_data_body) + decryptor.finalize()
    decrypted_data = json.loads(decrypted_data_bytes.decode("utf-8"))

    return decrypted_data, aes_key, iv

async def decrypt_media_content (
    encryption_metadata: str, cdn_url: str = None,
    media_content: str = None, client: httpx.AsyncClient = None
):
    """
    Downloads and decrypts encrypted media content from a given CDN URL.

    This function verifies the SHA256 hash and HMAC of the encrypted content, decrypts the media using AES-CBC with
    a provided IV, and validates the decrypted content hash against the provided plaintext hash.

    :param encryption_metadata: Dictionary containing encryption details (keys and hashes).
    :param cdn_url: The URL to download the encrypted media content from. Ignored if media_content is provided.
    :param media_content: Encrypted media content in bytes. If None, the content is downloaded from cdn_url.
    :param client: Optional HTTP client for making the download request.

    :return: The decrypted media content as a base64-encoded string.

    :raises ValueError: If hash or HMAC validation fails, or if neither cdn_url nor media_content are provided.
    """
    if media_content is None and cdn_url is None:
        raise ValueError("Either media_content or cdn_url must be provided.")

    # Decode necessary metadata fields
    encrypted_hash = base64.b64decode(encryption_metadata["encrypted_hash"])
    hmac_key = base64.b64decode(encryption_metadata["hmac_key"])
    iv = base64.b64decode(encryption_metadata["iv"])
    plaintext_hash = base64.b64decode(encryption_metadata["plaintext_hash"])
    encryption_key = base64.b64decode(encryption_metadata["encryption_key"])

    # Download media content if not provided
    if media_content is None:
        async with (client or httpx.AsyncClient()) as http_client:
            response = await http_client.get(cdn_url)
            media_content = response.content

    # Verify SHA256 hash of the encrypted media content
    if hashlib.sha256(media_content).digest() != encrypted_hash:
        raise ValueError("SHA256 hash verification failed for encrypted content.")

    # Separate ciphertext and HMAC from the media content
    ciphertext = media_content[:-10]  # Exclude last 10 bytes (HMAC)
    hmac_provided = media_content[-10:]

    # Validate HMAC of the encrypted media
    hmac_calculated = hmac.new(hmac_key, iv + ciphertext, hashlib.sha256).digest()[:10]
    if hmac_calculated != hmac_provided:
        raise ValueError("HMAC validation failed for encrypted content.")

    # Decrypt the ciphertext using AES-CBC
    cipher = Cipher(algorithms.AES(encryption_key), modes.CBC(iv) )
    decryptor = cipher.decryptor()
    decrypted_padded = decryptor.update(ciphertext) + decryptor.finalize()

    # Remove PKCS7 padding
    unpadder = PKCS7(algorithms.AES.block_size).unpadder()
    decrypted_media = unpadder.update(decrypted_padded) + unpadder.finalize()

    # Validate SHA256 hash of the decrypted media content
    if hashlib.sha256(decrypted_media).digest() != plaintext_hash:
        raise ValueError("Decrypted media hash validation failed.")

    # Return decrypted media content as a base64-encoded string
    return base64.b64encode(decrypted_media).decode("utf-8")

def generate_rsa_private_key (password: str) -> str:
    """
    Generates a private RSA key, encrypts it with Triple DES (DES-EDE3-CBC) and a password, 
    and returns it as a PEM-formatted string.

    :param password: Password to encrypt the private key.
    :return: Encrypted private key in PEM format as a string.
    """
    rsa_key = RSA.generate(2048)

    # Export private key in PEM format encrypted with DES3
    return rsa_key.export_key(
        format="PEM", passphrase=password, pkcs=1, protection="DES-EDE3-CBC"
    ).decode("utf-8")

def extract_public_key_from_private (private_key_pem: str, password: str) -> str:
    """
    Extracts the RSA public key from a private key PEM and returns it as a PEM-formatted string.

    :param private_key_pem: PEM-formatted private key as a string.
    :param password: Password to decrypt the private key.
    :return: Public key in PEM format as a string.
    """
    private_key = RSA.import_key(private_key_pem, passphrase=password)

    public_key = private_key.publickey()

    return public_key.export_key(format="PEM").decode("utf-8")
