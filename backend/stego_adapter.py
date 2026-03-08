import os
import struct
import tempfile
import sys
from stego import stego_api_wrappers

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

def get_aes_key(password_str: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    return kdf.derive(password_str.encode('utf-8'))

def encrypt_payload(payload: bytes, password: str) -> bytes:
    salt = os.urandom(16)
    key = get_aes_key(password, salt)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, payload, None)
    return salt + nonce + ciphertext

def decrypt_payload(encrypted_payload: bytes, password: str) -> bytes:
    if len(encrypted_payload) < 28:
        raise ValueError("Payload too short to be encrypted")
    salt = encrypted_payload[:16]
    nonce = encrypted_payload[16:28]
    ciphertext = encrypted_payload[28:]
    key = get_aes_key(password, salt)
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None)

def encode(cover_path: str, secret_text: str, secret_file: str, key: str, media_type: str, output_path: str, encrypt: bool = False) -> str:
    """Return output_path on success or raise an Exception."""
    
    # 1. Prepare secret_bytes
    if secret_file and os.path.exists(secret_file):
        with open(secret_file, 'rb') as f:
            payload_bytes = f.read()
        name_bytes = os.path.basename(secret_file).encode('utf-8')
    elif secret_text:
        payload_bytes = secret_text.encode('utf-8')
        name_bytes = b'message.txt'
    else:
        raise ValueError("Must provide either secret_text or secret_file")

    if not key:
        raise ValueError("Must provide a secret key")

    # 2. Package with custom internal header to preserve filename string during byte-decoding
    # Header format: 4 bytes naming length prefix -> filename characters -> payload...
    header = struct.pack('>I', len(name_bytes))
    full_payload_bytes = header + name_bytes + payload_bytes

    # AES encryption if requested
    if encrypt:
        # 0x01 flags that this payload is encrypted
        full_payload_bytes = b'\x01' + encrypt_payload(full_payload_bytes, key)
    else:
        # 0x00 flags that this payload is plainly encoded
        full_payload_bytes = b'\x00' + full_payload_bytes


    # 3. Pass to the new underlying API wrappers that natively integrate length and byte-level shuffles 
    try:
        if media_type == 'image':
            stego_api_wrappers.encode_image(cover_path, full_payload_bytes, key, output_path)
        elif media_type == 'audio':
            stego_api_wrappers.encode_audio(cover_path, full_payload_bytes, key, output_path)
        elif media_type == 'video':
            stego_api_wrappers.encode_video(cover_path, full_payload_bytes, key, output_path)
        else:
            raise ValueError(f"Unsupported media type: {media_type}")
    except ValueError:
        raise
    except Exception as e:
        raise Exception(f"Failed to encode: {str(e)}")

    if not os.path.exists(output_path):
        raise FileNotFoundError("Steganography encoding failed, output file not generated.")

    return output_path


def decode(stego_path: str, key: str, media_type: str) -> dict:
    """Return {'text': '...'} or {'file_path': '/tmp/...'}."""
    if not key:
        raise ValueError("Must provide a secret key")

    # Call simple wrapper API returning pure extracted bytes seamlessly 
    try:
        if media_type == 'image':
            extracted_bytes = stego_api_wrappers.decode_image(stego_path, key)
        elif media_type == 'audio':
            extracted_bytes = stego_api_wrappers.decode_audio(stego_path, key)
        elif media_type == 'video':
            extracted_bytes = stego_api_wrappers.decode_video(stego_path, key)
        else:
            raise ValueError(f"Unsupported media type: {media_type}")
    except ValueError:
        raise
    except Exception as e:
        raise Exception(f"Failed to decode: {str(e)}. Incorrect password or corrupt file.")

    if not extracted_bytes or len(extracted_bytes) < 5:
        raise ValueError("Empty or corrupted payload extraction.")

    # Determine encryption flag
    is_encrypted = extracted_bytes[0] == 1
    actual_payload = extracted_bytes[1:]

    # Decrypt if necessary
    if is_encrypted:
        try:
            actual_payload = decrypt_payload(actual_payload, key)
        except Exception as e:
            raise ValueError("AES Decryption failed. Incorrect password, missing tag, or corrupted file.")

    # Process internal header format back out
    name_len = struct.unpack('>I', actual_payload[:4])[0]
    if name_len > 1000 or len(actual_payload) < (4 + name_len):
        raise ValueError("Invalid decoded header lengths. Likely incorrect password or corrupted file.")
        
    name_bytes = actual_payload[4 : 4 + name_len]
    name = name_bytes.decode('utf-8', errors='replace')
    payload = actual_payload[4 + name_len:]

    # Result routing logic identical to previous version but sourced directly from memory bytes
    if name == 'message.txt':
        try:
            return {'text': payload.decode('utf-8')}
        except UnicodeDecodeError:
            pass 

    output_path = os.path.join(os.path.dirname(stego_path), f"decoded_{name}")
    with open(output_path, 'wb') as f:
        f.write(payload)

    return {'file_path': output_path, 'name': name}
