"""Configuración de pytest: inyecta secretos efímeros para las pruebas.

Los valores se generan en cada ejecución (nunca quedan en el repo), alineado
con docs/SECRETS.md §2. Deben definirse antes de importar securebank_api.
"""
import os
import secrets

os.environ.setdefault("SECUREBANK_JWT_SECRET", secrets.token_urlsafe(48))
os.environ.setdefault("SECUREBANK_DEMO_ALICE_PASSWORD", secrets.token_urlsafe(18))
os.environ.setdefault("SECUREBANK_DEMO_BOB_PASSWORD", secrets.token_urlsafe(18))
