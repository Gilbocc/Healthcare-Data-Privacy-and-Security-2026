import json
from pathlib import Path


root = Path(__file__).resolve().parent


def md(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip().splitlines(True)}


def code(text: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": text.strip().splitlines(True),
    }


def write_notebook(filename: str, title: str, cells: list[dict]) -> None:
    notebook = {
        "cells": [md(f"# {title}"), *cells],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    (root / filename).write_text(json.dumps(notebook, indent=2), encoding="utf-8")


write_notebook(
    "01_password_storage_and_cracking.ipynb",
    "Password Storage and Cracking",
    [
        md(
            """
## Goal

This notebook shows why authentication systems should not store plaintext passwords and why salted,
slow password verifiers are better than simple hashes.

The setting is St. Isidore Hospital. We create a few toy staff accounts, then simulate an attacker
who obtains a password file. This is a teaching model only. Real systems use mature identity
providers, password hashing libraries, MFA platforms, monitoring, and recovery procedures.
"""
        ),
        code(
            """
import hashlib
import hmac
import os
import time


# St. Isidore toy users. Some passwords are intentionally weak for the attack demo.
users = {
    "dr.moretti": "StIsidore2026!",
    "nurse.bianchi": "blue-river-calm-ward",
    "pharmacist.galli": "Pharmacy123!",
    "patient.rossi": "maria1968",
}

print("Toy users:", list(users))
"""
        ),
        md(
            """
## Bad design: plaintext password storage

Plaintext storage is dangerous because a database leak immediately becomes an account compromise.
The attacker does not need to crack anything.
"""
        ),
        code(
            """
# This is intentionally bad. Do not store passwords like this.
plaintext_password_file = users.copy()

for username, password in plaintext_password_file.items():
    print(f"{username:18s} -> {password}")
"""
        ),
        md(
            """
## Better design: salted PBKDF2 verifiers

The system stores a random salt and a derived verifier. At login, it recomputes the verifier from
the submitted password and compares it in constant time.
"""
        ),
        code(
            """
def make_verifier(password: str, iterations: int = 200_000) -> dict:
    # Generate a different salt for every password.
    salt = os.urandom(16)

    # Derive a slow password verifier with PBKDF2-HMAC-SHA256.
    verifier = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )

    # Store parameters needed for verification, not the plaintext password.
    return {"salt": salt, "iterations": iterations, "verifier": verifier}


def verify_password(password: str, record: dict) -> bool:
    # Recompute the verifier using the stored salt and iteration count.
    candidate = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        record["salt"],
        record["iterations"],
    )

    # Compare securely to avoid timing leaks in real implementations.
    return hmac.compare_digest(candidate, record["verifier"])


password_file = {username: make_verifier(password) for username, password in users.items()}

for username, record in password_file.items():
    print(username, record["salt"].hex(), record["verifier"].hex()[:24] + "...")
"""
        ),
        code(
            """
# A legitimate login recomputes the verifier and compares it with the stored value.
print("Correct password:", verify_password("blue-river-calm-ward", password_file["nurse.bianchi"]))
print("Wrong password:  ", verify_password("blue-river-calm-ward!", password_file["nurse.bianchi"]))
"""
        ),
        md(
            """
## Offline dictionary attack

If an attacker steals the password file, they can test guesses offline. Salts do not stop guessing,
but they prevent simple reuse of precomputed tables and force account-specific work.
"""
        ),
        code(
            """
# A small attacker dictionary. Real dictionaries contain millions or billions of guesses.
dictionary = [
    "admin",
    "password",
    "Password123!",
    "StIsidore2026!",
    "Pharmacy123!",
    "maria1968",
    "blue-river-calm-ward",
    "correct-horse-battery-staple",
]


def crack_account(username: str, record: dict, guesses: list[str]) -> str | None:
    # Try each candidate against the stolen verifier.
    for guess in guesses:
        if verify_password(guess, record):
            return guess
    return None


for username, record in password_file.items():
    cracked = crack_account(username, record, dictionary)
    print(f"{username:18s} -> {cracked}")
"""
        ),
        md(
            """
## Cost matters

Slow hashing increases the cost of each guess. Administrators must choose parameters that fit their
systems and policies. Too cheap helps attackers; too expensive can harm login availability.
"""
        ),
        code(
            """
def time_one_guess(iterations: int) -> float:
    # Build a record with the chosen iteration count.
    record = make_verifier("test-password", iterations=iterations)

    # Measure one verification attempt.
    start = time.perf_counter()
    verify_password("wrong-password", record)
    return time.perf_counter() - start


for iterations in [10_000, 50_000, 200_000]:
    elapsed = time_one_guess(iterations)
    print(f"{iterations:>7,d} iterations -> {elapsed:.4f} seconds per guess")
"""
        ),
        md(
            """
## Takeaway

Salted slow verifiers reduce the damage of a stolen password file, but they do not make weak
passwords safe. St. Isidore still needs password screening, rate limits, MFA for sensitive systems,
monitoring, and secure recovery.
"""
        ),
    ],
)


write_notebook(
    "02_challenge_response_replay.ipynb",
    "Challenge-Response and Replay",
    [
        md(
            """
## Goal

This notebook shows why sending a password, or even the same password hash, is replayable. Then it
shows the challenge-response idea: the client sends a value computed from a fresh nonce and a
password-derived secret, so the network message is different at every login.

The code is intentionally small so the mechanics are visible. Real remote authentication protocols
must also handle TLS, phishing, server authentication, device compromise, key management, logging,
and recovery.
"""
        ),
        code(
            """
import hashlib
import hmac
import os


# Shared secret for a toy clinician account.
username = "dr.moretti"
password = "blue-river-calm-ward"


def h(data: bytes) -> bytes:
    # A compact helper for SHA-256.
    return hashlib.sha256(data).digest()


# The client can derive this value after the user types the password.
client_password_hash = h(password.encode("utf-8"))

# The hospital server stores the corresponding verifier, not the plaintext password.
stored_password_hash = client_password_hash

print(username, "stored verifier:", stored_password_hash.hex()[:32] + "...")
"""
        ),
        md(
            """
## Static hash: replayable

If the client sends the same password hash every time, that hash becomes a \textbf{password
equivalent}. An attacker can capture it once and replay it without knowing the original password.
"""
        ),
        code(
            """
def static_hash_login_message(password: str) -> bytes:
    # This message is always the same for the same password.
    # It avoids sending plaintext, but it is still replayable.
    return h(password.encode("utf-8"))


captured_static_hash = static_hash_login_message(password)
print("Captured static hash:", captured_static_hash.hex()[:32] + "...")

# The attacker replays exactly the same bytes later.
replay_accepted = hmac.compare_digest(captured_static_hash, stored_password_hash)
print("Replay accepted?", replay_accepted)
"""
        ),
        md(
            """
## Challenge-response with a nonce

The server sends a fresh random nonce. The client computes a response over the nonce and the
password-derived value. The client does \textbf{not} send the password and does \textbf{not} send
the raw password hash. It sends a response that changes when the nonce changes.
"""
        ),
        code(
            """
def make_challenge() -> bytes:
    # A nonce should be unpredictable and should not be reused.
    return os.urandom(16)


def response_for_nonce(nonce: bytes, password_hash: bytes) -> bytes:
    # HMAC binds the response to this nonce and this password-derived value.
    # Different nonce, different transmitted response.
    return hmac.new(password_hash, nonce, hashlib.sha256).digest()


def server_accepts(nonce: bytes, response: bytes) -> bool:
    # The server recomputes the expected response from its stored verifier.
    expected = response_for_nonce(nonce, stored_password_hash)
    return hmac.compare_digest(response, expected)


nonce_1 = make_challenge()
response_1 = response_for_nonce(nonce_1, client_password_hash)

print("First login accepted?", server_accepts(nonce_1, response_1))
"""
        ),
        code(
            """
# A replay against a new nonce should fail.
nonce_2 = make_challenge()
print("Replay old response with new nonce accepted?", server_accepts(nonce_2, response_1))

# A fresh response for the new nonce should succeed.
response_2 = response_for_nonce(nonce_2, client_password_hash)
print("Fresh response accepted?", server_accepts(nonce_2, response_2))

print("Response 1:", response_1.hex()[:32] + "...")
print("Response 2:", response_2.hex()[:32] + "...")
print("Same password-derived value, different nonce, different response:", response_1 != response_2)
"""
        ),
        md(
            """
## Hospital interpretation

For St. Isidore remote EHR access, the important concept is freshness. The response must prove
knowledge of the password-derived secret for this login attempt, not for a login observed
yesterday. The password-derived value may be stable, but the transmitted response changes because
the nonce changes.
"""
        ),
    ],
)


write_notebook(
    "03_totp_mfa.ipynb",
    "TOTP Multi-Factor Authentication",
    [
        md(
            """
## Goal

This notebook demonstrates a time-based one-time password (TOTP) factor. TOTP uses a shared secret
and a time step to generate short codes.

This is still only a teaching model. Production MFA should be delivered through a mature identity
provider or MFA product, with enrollment, revocation, recovery, monitoring, and phishing-resistant
options where appropriate.
"""
        ),
        code(
            """
import time

import pyotp


# During enrollment, the hospital server creates a per-user secret.
secret = pyotp.random_base32()
username = "dr.moretti"

# The same secret is stored by the user's authenticator app.
totp = pyotp.TOTP(secret, interval=30)

print("User:", username)
print("Enrollment secret:", secret)
print("Current code:", totp.now())
"""
        ),
        md(
            """
## Verifying a current code

The server accepts the code only if it matches the expected value for the current time step.
"""
        ),
        code(
            """
# Simulate a code typed by the user from the authenticator app.
submitted_code = totp.now()

# The server verifies the submitted code against the shared secret and current time.
print("Submitted:", submitted_code)
print("Accepted?", totp.verify(submitted_code))
"""
        ),
        md(
            """
## Time windows and clock drift

Hospitals may allow a small adjacent time window to tolerate clock drift or network delay. A wider
window improves usability but also increases the period in which a captured code may work.
"""
        ),
        code(
            """
current_time = int(time.time())

# Generate the previous, current, and next 30-second window codes.
for offset in [-30, 0, 30]:
    code_for_window = totp.at(current_time + offset)
    accepted_strict = totp.verify(code_for_window, for_time=current_time, valid_window=0)
    accepted_with_drift = totp.verify(code_for_window, for_time=current_time, valid_window=1)
    print(
        f"offset {offset:+4d}s",
        code_for_window,
        "strict=", accepted_strict,
        "drift_window=", accepted_with_drift,
    )
"""
        ),
        md(
            """
## Captured OTPs are time-limited, not phishing-proof

An OTP expires quickly, but a real-time phishing site can relay it immediately. This is why
phishing-resistant MFA, such as FIDO2/passkeys or hardware security keys, is stronger for
administrator and remote-access accounts.
"""
        ),
        code(
            """
# Simulate a captured code.
captured_code = totp.now()
print("Captured code:", captured_code)
print("Useful right now?", totp.verify(captured_code))

# In a live notebook, wait until the code changes and run the next line again.
# The old code will eventually fail outside the accepted verification window.
print("Current code after time passes:", totp.now())
"""
        ),
        md(
            """
## Takeaway

TOTP is a useful second factor, but it depends on shared-secret protection, time synchronization,
safe enrollment, safe recovery, and endpoint security. It improves St. Isidore's authentication, but
it does not eliminate phishing or compromised-device risk.
"""
        ),
    ],
)


print(f"Wrote notebooks in {root}")
