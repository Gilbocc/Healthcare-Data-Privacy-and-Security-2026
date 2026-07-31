# Lesson 05 Authentication Examples

These notebooks are toy examples for teaching authentication concepts. They are not production
authentication systems. Real healthcare systems should use mature identity providers, operating
system authentication, database authentication, MFA platforms, access-management products, and
audited recovery procedures. System administrators normally configure policies and integrations;
they do not hand-code authentication mechanisms inside application notebooks.

Create and use the local virtual environment from `lesson-05`:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r examples/requirements.txt
```

Open the notebooks with VS Code, JupyterLab, or another notebook UI, and select `lesson-05/.venv`
as the Python interpreter/kernel.

The notebooks use the St. Isidore Hospital scenario and cover:

- `01_password_storage_and_cracking.ipynb`: plaintext storage, salted PBKDF2 verifiers, and a
  dictionary attack against weak hospital-themed passwords.
- `02_challenge_response_replay.ipynb`: replayable static authentication, nonce-based
  challenge-response, and why old responses should fail.
- `03_totp_mfa.ipynb`: shared-secret enrollment, TOTP generation, verification windows, clock
  drift, and a short discussion of phishing limits.
