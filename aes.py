from Cryptodome.Cipher import AES
from base64 import b64decode, b64encode

BLOCK_SIZE = 16
pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * chr(BLOCK_SIZE - len(s) % BLOCK_SIZE)
unpad = lambda s: s[:-ord(s[len(s) - 1:])]


def encrypt(plain_text, key, IV):
    plain_text = pad(plain_text)
    cipher = AES.new(key.encode(), AES.MODE_CBC, IV.encode())
    encrypted = cipher.encrypt(plain_text.encode())

    return b64encode(encrypted).decode()


def decrypt(cipher_text, key, IV):
    cipher_text = b64decode(cipher_text)
    cipher = AES.new(key.encode(), AES.MODE_CBC, IV.encode())
    return unpad(cipher.decrypt(cipher_text))


if __name__ == '__main__':
    key = "AnyRandomInsecure256bitLongKeyXX"

    encrypted = encrypt("15.00", key, 'This is an IV456')
    decrypted = decrypt(encrypted, key, 'This is an IV456')
    print(f"{encrypted} <-> {decrypted.decode()}")