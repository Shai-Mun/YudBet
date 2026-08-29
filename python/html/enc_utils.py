__author__ = 'Yossi'

# DPH
import random

# AES
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes

# RSA
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend

SIZE_HEADER_FORMAT = "0000000|"  # n digits for data size + one delimiter
size_header_size = len(SIZE_HEADER_FORMAT)
TCP_DEBUG = True
LEN_TO_PRINT = 100


# ------------------------------------------------------------------------------------------------------------------
# DPH
# ------------------------------------------------------------------------------------------------------------------
def dph_serv(sock):
    with open('big_prime.txt', 'r') as f:
        p = int(f.read()[2:])
    g = 3  # alpha
    send_msg(sock, f"{p},{g}".encode())

    x = random.randint(2, p - 2)
    a = pow(g, x, p)
    send_msg(sock, str(a).encode())

    b = int(recv_msg(sock).decode())

    encryption_key = str(pow(b, x, p))
    print(f"the key is: {encryption_key}")
    return encryption_key


def dph_cli(sock):
    send_msg(sock, "DPH".encode())

    parameters = recv_msg(sock).decode()
    parts = parameters.split(',')
    p = int(parts[0])
    g = int(parts[1])  # alpha

    y = random.randint(2, p - 2)
    b = pow(g, y, p)
    send_msg(sock, str(b).encode())

    a = int(recv_msg(sock).decode())

    encryption_key = str(pow(a, y, p))
    # print(f"the key is: {encryption_key}")
    return encryption_key


# ------------------------------------------------------------------------------------------------------------------
# RSA
# ------------------------------------------------------------------------------------------------------------------
def rsa_serv(sock):
    private_key, public_key = generate_rsa_keys()

    public_key_pem = get_public_key_pem(public_key)
    send_msg(sock, public_key_pem)
    ciphertext = recv_msg(sock)
    plaintext = rsa_decrypt(private_key, ciphertext)
    print(f"[*] original key: \"{plaintext}\"")
    print(f"[+] Decrypted key: \"{plaintext.decode()}\"")
    return plaintext.decode()


def rsa_cli(sock):
    send_with_size(sock, "RSA".encode())

    encryption_key = "SecretMessage123"

    public_key_pem = recv_msg(sock)
    public_key = load_public_key_pem(public_key_pem)
    ciphertext = rsa_encrypt(public_key, encryption_key.encode("utf-8"))
    send_msg(sock, ciphertext)
    print(f"[*] Original key: \"{encryption_key}\"")
    print(f"[*] Encrypted key (hex): {ciphertext.hex()[:60]}...")
    return encryption_key


# Key Generation
def generate_rsa_keys():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    public_key = private_key.public_key()
    return private_key, public_key


# Key Serialization
def get_public_key_pem(public_key) -> bytes:
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )


def load_public_key_pem(pem: bytes):
    return serialization.load_pem_public_key(
        pem,
        backend=default_backend()
    )


# RSA Encrypt / Decrypt
def rsa_encrypt(public_key, message: bytes) -> bytes:
    return public_key.encrypt(
        message,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )


def rsa_decrypt(private_key, ciphertext: bytes) -> bytes:
    return private_key.decrypt(
        ciphertext,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )


# Send / Receive with length prefix
def send_msg(sock, data: bytes):
    sock.sendall(len(data).to_bytes(4, "big") + data)


def recv_msg(sock) -> bytes:
    raw_len = _recv_exact(sock, 4)
    msg_len = int.from_bytes(raw_len, "big")
    return _recv_exact(sock, msg_len)


def _recv_exact(sock, n: int) -> bytes:
    data = b""
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            raise ConnectionError("החיבור נסגר באמצע קבלת הנתונים")
        data += chunk
    return data


# ------------------------------------------------------------------------------------------------------------------
# AES
# ------------------------------------------------------------------------------------------------------------------
def aes_cbc_encrypt(msg, secret: str):
    if TCP_DEBUG:
        print(f"Sent: {msg}")

    key = hashlib.sha256(secret.encode()).digest()
    iv = get_random_bytes(16)  # וקטור אתחול אקראי
    cipher = AES.new(key, AES.MODE_CBC, iv)

    if isinstance(msg, str):
        msg = msg.encode()
    ct_bytes = cipher.encrypt(pad(msg, AES.block_size))

    return ct_bytes, iv


def aes_cbc_decrypt(ciphertext, iv, secret):
    key = hashlib.sha256(secret.encode()).digest()
    cipher = AES.new(key, AES.MODE_CBC, iv)

    msg = cipher.decrypt(ciphertext)
    try:
        msg = unpad(msg, AES.block_size)
        if TCP_DEBUG:
            print(f"Received: {msg}")

    except ValueError:
        return 'Invalid padding or wrong key'
    return msg


# ------------------------------------------------------------------------------------------------------------------
# TCP BY SIZE
# ------------------------------------------------------------------------------------------------------------------
def recv_by_size(sock, key = ""):
    size_header = b''
    data_len = 0
    while len(size_header) < size_header_size:
        _s = sock.recv(size_header_size - len(size_header))
        if _s == b'':
            size_header = b''
            break
        size_header += _s
    data = b''
    if size_header != b'':
        data_len = int(size_header[:size_header_size - 1])
        while len(data) < data_len:
            _d = sock.recv(data_len - len(data))
            if _d == b'':
                data = b''
                break
            data += _d

    if data_len != len(data):
        return b''  # Partial data is like no data !

    if key != "" and data:
        data = aes_cbc_decrypt(data[16:], data[:16], key)
    if TCP_DEBUG and size_header != b'':
        print("\nRecv(%s)>>>" % (size_header,), end='')
        print("%s" % (data[:min(len(data), LEN_TO_PRINT)],))

    return data


def send_with_size(sock, bdata, key=""):
    if isinstance(bdata, str):
        bdata = bdata.encode()

    tmp = bdata
    tmp_len = len(bdata)
    tmp_header = str(tmp_len).zfill(size_header_size - 1) + "|"

    if key != "":
        bdata, iv = aes_cbc_encrypt(bdata, key)
        bdata = iv + bdata

    len_data = len(bdata)
    header_data = str(len_data).zfill(size_header_size - 1) + "|"

    bytea = bytearray(header_data,encoding='utf8') + bdata
    sock.send(bytea)
    if TCP_DEBUG and len_data > 0:
        bytea = bytearray(tmp_header,encoding='utf8') + tmp
        print("\nSent(%s)>>>" % (len_data,), end='')
        print("%s" % (bytea[:min(len(bytea), LEN_TO_PRINT)],))








