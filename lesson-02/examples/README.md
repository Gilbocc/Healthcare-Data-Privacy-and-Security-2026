# Lesson 02 Notebooks

Run from `lesson-02`:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Open the notebooks with VS Code, JupyterLab, or another notebook UI, and select `lesson-02/.venv`
as the Python interpreter/kernel. The local `.venv` contains the cryptographic libraries used by
the examples.

The notebooks use a St. Isidore Hospital scenario and cover:

- `01_classical_caesar_cipher.ipynb`: Caesar cipher and frequency leakage.
- `02_des_3des_mechanics.ipynb`: DES/3DES, fixed blocks, padding, CBC, and a toy Feistel network.
- `03_aes_modes_authenticated_encryption.ipynb`: AES-ECB leakage, AES-CBC, and AES-GCM.
- `04_stream_cipher_chacha20.ipynb`: ChaCha20 and nonce reuse.
- `05_hashes_hmac_passwords.ipynb`: SHA-256, HMAC, and password hashing.
- `06_rsa_signatures_digital_envelopes.ipynb`: RSA signatures and hybrid encryption.
- `07_diffie_hellman_randomness.ipynb`: finite-field Diffie-Hellman key agreement and cryptographic randomness.
