from Cryptodome import Random
from Cryptodome.Cipher import AES
from nacl.public import PublicKey, SealedBox
import binascii
import struct
import base64
import time

class InstagramCrypto:
    def __init__(self, encryption_config):
        self.key_id = encryption_config.get("key_id")
        self.pub_key_hex = encryption_config.get("public_key")
        self.version_str = encryption_config.get("version")

        if not all([self.key_id, self.pub_key_hex, self.version_str]):
            raise ValueError("instagram encryption configuration is incomplete.")

    def encrypt_password(self, password_plain):
        """encrypts the password according to instagram's encryption method."""
        try:
            key = Random.get_random_bytes(32)
            iv = bytes([0] * 12)
            current_time = int(time.time())

            aes = AES.new(key, AES.MODE_GCM, nonce=iv, mac_len=16)
            aes.update(str(current_time).encode("utf-8"))
            encrypted_password_aes_output, cipher_tag = aes.encrypt_and_digest(password_plain.encode("utf-8"))

            pub_key_bytes = binascii.unhexlify(self.pub_key_hex)
            seal_box = SealedBox(PublicKey(pub_key_bytes))
            encrypted_key_sealed_box_output = seal_box.encrypt(key)

            shared_secret = None
            if len(encrypted_key_sealed_box_output) == 80:
                shared_secret = encrypted_key_sealed_box_output
            elif len(encrypted_key_sealed_box_output) > 80:
                print(f"[Crypto Warning] pynacl sealedbox output ({len(encrypted_key_sealed_box_output)} bytes) is longer than 80 bytes. truncating to 80 bytes. this may cause failure.")
                shared_secret = encrypted_key_sealed_box_output[:80]
            else:
                print(f"[Crypto Error] pynacl sealedbox output ({len(encrypted_key_sealed_box_output)} bytes) is shorter than 80 bytes. cannot proceed.")
                return None
            
            if shared_secret is None:
                return None
            
            key_id_byte = int(self.key_id).to_bytes(1, 'big')
            len_encrypted_key_bytes = struct.pack("<h", len(shared_secret))

            y_bytes_list = [
                bytes([1]),
                key_id_byte,
                len_encrypted_key_bytes,
                shared_secret,
                cipher_tag,
                encrypted_password_aes_output
            ]
            final_binary_payload = b''.join(y_bytes_list)

            base64_encoded_payload = base64.b64encode(final_binary_payload).decode('utf-8')

            final_enc_password = f"#PWD_INSTAGRAM_BROWSER:{self.version_str}:{current_time}:{base64_encoded_payload}"
            
            return final_enc_password

        except Exception as e:
            print(f"[Crypto Error] failed to encrypt password: {e}")
            return None