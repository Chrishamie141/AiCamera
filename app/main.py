from flask import Flask, jsonify
from backend.app.routes import api
from backend.db.db import init_db


def create_app():
    print("[SYSTEM] Initializing database...")
    init_db()

    app = Flask(__name__)

    print("[SYSTEM] Registering API routes...")
    app.register_blueprint(api)

    @app.route("/")
    def home():
        return jsonify({
            "status": "AI Intrusion Detection API running",
            "endpoints": [
                "/api/stream",
                "/api/events",
                "/api/stats"
            ]
        })

    return app


def main():
    app = create_app()

    print("[SYSTEM] Starting AI Intrusion Detection server...")
    print("[SYSTEM] Camera stream available at: http://localhost:5000/api/stream")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        threaded=True
    )


if __name__ == "__main__":
    main()