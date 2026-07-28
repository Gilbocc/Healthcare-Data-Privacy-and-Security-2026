import json
from pathlib import Path


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip().splitlines(True)}


def code(text):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": text.strip().splitlines(True),
    }


def write_notebook(path, title, cells):
    notebook = {
        "cells": [
            md(f"# {title}\n\nThese examples use the running scenario of St. Isidore Hospital. They are teaching examples: understand the mechanism, then prefer well-reviewed libraries and current protocols in production.")
        ]
        + cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    path.write_text(json.dumps(notebook, indent=2), encoding="utf-8")


root = Path(__file__).parent

write_notebook(
    root / "01_classical_caesar_cipher.ipynb",
    "Classical Encryption: Caesar Cipher and Frequency Leakage",
    [
        md("## Goal\n\nA Caesar cipher is intentionally weak, but it shows the basic encryption idea: a plaintext is transformed by a rule and a key. Here the key is the shift amount."),
        code(
            """
import string

# Limit the toy cipher to uppercase English letters so the shift is easy to see.
ALPHABET = string.ascii_uppercase

def caesar(text, shift):
    out = []
    for ch in text.upper():
        if ch in ALPHABET:
            # Move alphabetic characters forward or backward by the key value.
            out.append(ALPHABET[(ALPHABET.index(ch) + shift) % 26])
        else:
            # Keep spaces and punctuation unchanged so the example remains readable.
            out.append(ch)
    return "".join(out)

message = "PATIENT MARIA ROSSI HAS BLOOD TYPE A POSITIVE"
ciphertext = caesar(message, 3)  # The key is the shift: 3.
print(ciphertext)  # Encrypted message.
print(caesar(ciphertext, -3))  # Decrypt by applying the inverse shift.
"""
        ),
        md("## Why It Fails\n\nThe cipher preserves language patterns. In a hospital, repeated words such as PATIENT, WARD, BLOOD, or RESULT would create clues."),
        code(
            """
from collections import Counter

# Count letters in the ciphertext; weak ciphers preserve useful statistics.
letters = [ch for ch in ciphertext if ch in ALPHABET]
print(Counter(letters).most_common())

# Brute force is trivial because Caesar has only 26 possible keys.
for guess in range(26):
    trial = caesar(ciphertext, -guess)
    if "PATIENT" in trial or "BLOOD" in trial:
        print("Likely key:", guess, "->", trial)
"""
        ),
    ],
)

write_notebook(
    root / "02_des_3des_mechanics.ipynb",
    "DES and 3DES: Blocks, Rounds, Padding, and Legacy Risk",
    [
        md("## Goal\n\nDES is obsolete, but it is useful historically because it shows a block cipher as repeated rounds over fixed-size blocks. Real DES uses initial/final permutations, expansion, key mixing, S-box substitution, and permutation across 16 Feistel rounds."),
        code(
            """
from Crypto.Cipher import DES, DES3
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes

record = b"Patient 2048: oncology appointment at 09:30"
print("Plaintext length:", len(record))
print("DES block size:", DES.block_size)

des_key = b"8bytekey"  # DES requires exactly 8 bytes; only 56 bits are effective.
iv = get_random_bytes(DES.block_size)  # CBC needs a fresh unpredictable IV.
cipher = DES.new(des_key, DES.MODE_CBC, iv)  # CBC chains each block to the previous ciphertext block.
ct = cipher.encrypt(pad(record, DES.block_size))  # Padding extends the message to a full block.
print("IV:", iv.hex())
print("Ciphertext:", ct.hex())

decipher = DES.new(des_key, DES.MODE_CBC, iv)  # Decryption needs the same key and IV.
print(unpad(decipher.decrypt(ct), DES.block_size))  # Remove padding after decryption.
"""
        ),
        md("## What DES Does Internally\n\nThe next cell is not full DES. It is a miniature Feistel network that mirrors the shape of DES: split the block, transform one side with a round key, XOR it into the other side, then swap. The same structure decrypts by applying round keys in reverse."),
        code(
            """
def toy_round_function(right, round_key):
    # This is not DES. It is only a keyed mixing function for the toy Feistel demo.
    return ((right ^ round_key) * 0x45D9F3B) & 0xFFFFFFFF

def toy_feistel_encrypt(block64, round_keys):
    # Split one 64-bit block into two 32-bit halves.
    left = (block64 >> 32) & 0xFFFFFFFF
    right = block64 & 0xFFFFFFFF
    trace = []
    for k in round_keys:
        new_left = right  # Feistel swap: old right becomes new left.
        new_right = left ^ toy_round_function(right, k)  # Mix old left with F(old right, key).
        left, right = new_left, new_right
        trace.append((left, right))
    return ((left << 32) | right), trace

def toy_feistel_decrypt(block64, round_keys):
    # Feistel decryption uses the same structure with round keys in reverse order.
    left = (block64 >> 32) & 0xFFFFFFFF
    right = block64 & 0xFFFFFFFF
    for k in reversed(round_keys):
        old_right = left  # Undo the swap from encryption.
        old_left = right ^ toy_round_function(old_right, k)  # Recover the previous left half.
        left, right = old_left, old_right
    return (left << 32) | right

block = int.from_bytes(b"LABRSLT1", "big")  # One 8-byte hospital-flavored block.
keys = [0x11111111, 0x22222222, 0x33333333, 0x44444444]  # Toy round keys.
encrypted, trace = toy_feistel_encrypt(block, keys)
print("Plain block:", hex(block))
for i, (l, r) in enumerate(trace, 1):
    print(f"Round {i}: L={l:08x} R={r:08x}")
print("Encrypted:", hex(encrypted))
print("Decrypted:", toy_feistel_decrypt(encrypted, keys).to_bytes(8, "big"))
"""
        ),
        md("## 3DES\n\n3DES applies DES three times. It was a migration path, not a modern choice. New systems should use AES or authenticated encryption modes instead."),
        code(
            """
key_3des = DES3.adjust_key_parity(get_random_bytes(24))  # 3DES uses DES keys with parity bits.
iv_3des = get_random_bytes(DES3.block_size)  # Fresh IV for CBC mode.
triple = DES3.new(key_3des, DES3.MODE_CBC, iv_3des)  # 3DES applies DES operations multiple times.
ct3 = triple.encrypt(pad(record, DES3.block_size))
plain3 = unpad(DES3.new(key_3des, DES3.MODE_CBC, iv_3des).decrypt(ct3), DES3.block_size)
print(ct3.hex())
print(plain3)
"""
        ),
    ],
)

write_notebook(
    root / "03_aes_modes_authenticated_encryption.ipynb",
    "AES: ECB Leakage, CBC, and GCM Authenticated Encryption",
    [
        md("## Goal\n\nAES is a modern symmetric block cipher. The dangerous part for students to see is that the mode matters: AES-ECB leaks repeated patterns, while authenticated modes such as AES-GCM provide confidentiality and integrity."),
        code(
            """
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

block = b"ICU-ROOM-07-ABCD"  # exactly 16 bytes
plaintext = block * 6  # Repetition makes ECB leakage visible.
key = get_random_bytes(16)  # 16 bytes = 128-bit AES key.

ecb = AES.new(key, AES.MODE_ECB)  # ECB encrypts each block independently.
ct_ecb = ecb.encrypt(plaintext)  # No padding needed: plaintext is already block-aligned.
chunks = [ct_ecb[i:i+16].hex() for i in range(0, len(ct_ecb), 16)]
print("ECB blocks:")
for c in chunks:
    print(c)
print("Unique blocks:", len(set(chunks)), "of", len(chunks))
"""
        ),
        code(
            """
clinical_note = b"Patient 2048: discharge summary, diagnosis, medications, allergies."

cbc_key = get_random_bytes(16)  # Use a fresh key for the CBC example.
iv = get_random_bytes(16)  # CBC requires a fresh IV.
cbc = AES.new(cbc_key, AES.MODE_CBC, iv)
ct_cbc = cbc.encrypt(pad(clinical_note, AES.block_size))  # Pad because notes are not block-aligned.
recovered = unpad(AES.new(cbc_key, AES.MODE_CBC, iv).decrypt(ct_cbc), AES.block_size)
print("CBC ciphertext:", ct_cbc.hex())
print(recovered)
"""
        ),
        md("## AES-GCM\n\nGCM is usually a better teaching default because it returns both ciphertext and an authentication tag. If the ciphertext or associated metadata changes, verification fails."),
        code(
            """
gcm_key = get_random_bytes(32)  # 32 bytes = 256-bit AES key.
nonce = get_random_bytes(12)  # GCM commonly uses a 12-byte nonce; do not reuse it with this key.
aad = b"EHR-message:lab-result:v1"  # Associated data is authenticated but not encrypted.

gcm = AES.new(gcm_key, AES.MODE_GCM, nonce=nonce)
gcm.update(aad)  # Bind metadata to the ciphertext.
ct, tag = gcm.encrypt_and_digest(clinical_note)  # Encrypt and compute the authentication tag.
print("Ciphertext:", ct.hex())
print("Tag:", tag.hex())

verify = AES.new(gcm_key, AES.MODE_GCM, nonce=nonce)
verify.update(aad)  # Verification must use the same associated data.
print(verify.decrypt_and_verify(ct, tag))  # Raises ValueError if ciphertext or tag is invalid.

tampered = bytearray(ct)
tampered[0] ^= 1  # Flip one bit to simulate an attacker modifying the ciphertext.
try:
    verify = AES.new(gcm_key, AES.MODE_GCM, nonce=nonce)
    verify.update(aad)
    verify.decrypt_and_verify(bytes(tampered), tag)
except ValueError as exc:
    print("Tampering detected:", exc)
"""
        ),
    ],
)

write_notebook(
    root / "04_stream_cipher_chacha20.ipynb",
    "Stream Encryption: ChaCha20 and Keystream Safety",
    [
        md("## Goal\n\nA stream cipher generates a keystream and combines it with plaintext. The key lesson is nonce uniqueness: reusing the same key and nonce can reveal relationships between messages."),
        code(
            """
from Crypto.Cipher import ChaCha20
from Crypto.Random import get_random_bytes

key = get_random_bytes(32)  # ChaCha20 uses a 256-bit key in this library.
nonce = get_random_bytes(8)  # The nonce selects a unique keystream for this message.
msg = b"Telemetry: infusion pump dose=4.0 ml/h"

cipher = ChaCha20.new(key=key, nonce=nonce)  # Create the keystream generator.
ct = cipher.encrypt(msg)  # Encryption XORs plaintext with the keystream.
plain = ChaCha20.new(key=key, nonce=nonce).decrypt(ct)  # Decryption XORs with the same keystream.
print(ct.hex())
print(plain)
"""
        ),
        code(
            """
def xor_bytes(a, b):
    # XOR two byte strings up to the length of the shorter one.
    return bytes(x ^ y for x, y in zip(a, b))

m1 = b"Lab result patient 2048: potassium normal"
m2 = b"Lab result patient 2048: potassium urgent"
bad_nonce = b"12345678"  # Deliberately reused: this is the mistake.

c1 = ChaCha20.new(key=key, nonce=bad_nonce).encrypt(m1)  # First message under reused keystream.
c2 = ChaCha20.new(key=key, nonce=bad_nonce).encrypt(m2)  # Second message under the same keystream.
print("XOR ciphertexts equals XOR plaintexts:")
print(xor_bytes(c1, c2) == xor_bytes(m1, m2))
print(xor_bytes(c1, c2))
"""
        ),
    ],
)

write_notebook(
    root / "05_hashes_hmac_passwords.ipynb",
    "Hashes, HMAC, and Password Hashing",
    [
        md("## Goal\n\nHashes detect change, HMAC authenticates a message with a shared secret, and password hashing deliberately slows attackers down."),
        code(
            """
import hashlib

report = b"Radiology report for patient 2048: no fracture."
digest = hashlib.sha256(report).hexdigest()  # Hash the exact byte sequence.
print(digest)

changed = b"Radiology report for patient 2048: fracture."
print(hashlib.sha256(changed).hexdigest())  # A small content change gives a different digest.
"""
        ),
        code(
            """
import hmac
from secrets import token_bytes

mac_key = token_bytes(32)  # Shared secret used only by sender and receiver.
message = b"LAB|patient=2048|test=HbA1c|value=6.8"
tag = hmac.new(mac_key, message, hashlib.sha256).hexdigest()  # Authenticate message bytes.
print(tag)

received = b"LAB|patient=2048|test=HbA1c|value=8.8"
received_tag = hmac.new(mac_key, received, hashlib.sha256).hexdigest()  # Recompute on received data.
print("Valid?", hmac.compare_digest(tag, received_tag))  # Constant-time comparison avoids leaks.
"""
        ),
        code(
            """
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.backends import default_backend
import os

password = b"CorrectHorseBatteryStaple!"
salt = os.urandom(16)  # Unique salt prevents identical passwords from having identical hashes.
kdf = Scrypt(salt=salt, length=32, n=2**14, r=8, p=1, backend=default_backend())  # Slow KDF.
password_hash = kdf.derive(password)  # Store this verifier, not the plaintext password.
print("salt:", salt.hex())
print("stored hash:", password_hash.hex())
"""
        ),
    ],
)

write_notebook(
    root / "06_rsa_signatures_digital_envelopes.ipynb",
    "RSA, Digital Signatures, and Digital Envelopes",
    [
        md("## Goal\n\nPublic-key cryptography is slower than symmetric encryption but solves different problems: sending a secret to someone whose public key you know, and verifying who signed a message."),
        code(
            """
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

doctor_private = rsa.generate_private_key(public_exponent=65537, key_size=2048)  # Doctor's signing key.
doctor_public = doctor_private.public_key()  # Verifiers can know this key.
hospital_private = rsa.generate_private_key(public_exponent=65537, key_size=2048)  # Recipient secret.
hospital_public = hospital_private.public_key()  # Senders use this to protect data for the hospital.
"""
        ),
        code(
            """
message = b"Prescription approval for patient 2048"
signature = doctor_private.sign(
    message,
    # PSS is a randomized RSA signature padding scheme.
    padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
    hashes.SHA256(),
)

doctor_public.verify(
    signature,
    message,
    # Verification repeats the padding/hash checks with the public key.
    padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
    hashes.SHA256(),
)
print("Signature verified")
"""
        ),
        md("## Digital Envelope\n\nThe message is encrypted with a fresh AES key. The AES key is then encrypted with the recipient public key."),
        code(
            """
clinical_file = b"Discharge summary: diagnosis, therapy, follow-up, patient identifiers."
session_key = AESGCM.generate_key(bit_length=256)  # Fresh symmetric key for this file.
nonce = os.urandom(12)  # Fresh AES-GCM nonce.
aesgcm = AESGCM(session_key)
ciphertext = aesgcm.encrypt(nonce, clinical_file, b"recipient=hospital")  # Encrypt and authenticate.

wrapped_key = hospital_public.encrypt(
    session_key,
    # OAEP is modern RSA encryption padding for wrapping small secrets such as session keys.
    padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
)

unwrapped_key = hospital_private.decrypt(
    wrapped_key,
    # Only the hospital private key can recover the session key.
    padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
)
recovered = AESGCM(unwrapped_key).decrypt(nonce, ciphertext, b"recipient=hospital")  # Verify and decrypt.
print(recovered)
"""
        ),
    ],
)

write_notebook(
    root / "07_diffie_hellman_randomness.ipynb",
    "Diffie-Hellman and Cryptographic Randomness",
    [
        md("## Goal\n\nDiffie-Hellman lets two parties derive the same shared secret over an insecure network. This notebook uses a small finite-field example for visibility; real systems use much larger approved parameters. Randomness supplies private exponents, nonces, and session keys. Weak randomness weakens everything built on top."),
        code(
            """
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
import os, secrets, random

# Small teaching parameters: use large approved groups in production.
p = 23  # Public prime modulus.
g = 5   # Public generator.

# Each side chooses a private exponent and never sends it.
doctor_private = secrets.randbelow(p - 2) + 1
hospital_private = secrets.randbelow(p - 2) + 1

# Public values can travel over the network.
doctor_public = pow(g, doctor_private, p)
hospital_public = pow(g, hospital_private, p)

# Each side combines its private exponent with the other side's public value.
doctor_shared = pow(hospital_public, doctor_private, p)
hospital_shared = pow(doctor_public, hospital_private, p)
print(doctor_shared == hospital_shared)

session_key = HKDF(
    algorithm=hashes.SHA256(),
    length=32,
    salt=None,
    info=b"St Isidore VPN session",  # Context string binds the derived key to this purpose.
).derive(doctor_shared.to_bytes(2, "big"))  # Convert the shared number to bytes for the KDF.
print(session_key.hex())
"""
        ),
        code(
            """
print("Cryptographic token:", secrets.token_hex(16))  # Use secrets for security tokens.

random.seed(42)  # A fixed seed makes random predictable.
print("Predictable token:", hex(random.getrandbits(128)))
random.seed(42)  # Resetting the seed repeats the same output.
print("Same predictable token:", hex(random.getrandbits(128)))

print("OS randomness:", os.urandom(16).hex())  # OS randomness is suitable for crypto seeds/keys.
"""
        ),
    ],
)

print(f"Wrote notebooks in {root}")
