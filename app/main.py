import logging

from flask import Flask, jsonify, send_from_directory

from app.routes import api
from app.services import repository
from db.db import get_settings, init_db


def create_app() -> Flask:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    init_db()
    repository.run_retention(int(get_settings().get("retention_days", 14)))

    app = Flask(__name__, static_folder="../frontend/dist", static_url_path="/")
    app.register_blueprint(api)

    @app.route("/")
    def home():
        return jsonify({"status": "Smart Arrival Camera API", "frontend": "/dashboard"})

    @app.route("/dashboard")
    def dashboard():
        try:
            return send_from_directory(app.static_folder, "index.html")
        except Exception:
            return jsonify({"message": "Frontend build not found. Run frontend dev server."}), 404

    return app


def main() -> None:
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)


if __name__ == "__main__":
    main()
