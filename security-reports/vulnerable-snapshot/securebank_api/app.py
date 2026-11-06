"""
SecureBank API — app factory.

Proyecto transversal SecurePipeline (UBO · Sistemas Automatizados
DevSecOps). Ensambla los blueprints de cada dominio funcional y aplica
cabeceras de seguridad transversales (HSTS, nosniff, frame-deny).
"""
from flask import Flask, jsonify

from . import users, accounts, transfer, export, view, calc


def create_app() -> Flask:
    app = Flask(__name__)

    app.register_blueprint(users.bp)
    app.register_blueprint(accounts.bp)
    app.register_blueprint(transfer.bp)
    app.register_blueprint(export.bp)
    app.register_blueprint(view.bp)
    app.register_blueprint(calc.bp)

    @app.after_request
    def set_security_headers(response):
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    @app.get("/health")
    def health():
        return jsonify({"status": "ok", "service": "securebank-api"}), 200

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=5000)
