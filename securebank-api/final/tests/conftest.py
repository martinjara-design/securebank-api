"""Variables de entorno de prueba (los secretos reales nunca van en el repo).

El secreto JWT se genera aleatoriamente en cada ejecución. Las contraseñas
demo son fixtures de test, no credenciales reales (allowlist en .gitleaks.toml).
"""
import os
import secrets

os.environ.setdefault("SECUREBANK_JWT_SECRET", secrets.token_hex(32))
os.environ.setdefault("SECUREBANK_DEMO_ALICE_PW", "Alice#2026Secure")
os.environ.setdefault("SECUREBANK_DEMO_BOB_PW", "Bob#2026Secure")
