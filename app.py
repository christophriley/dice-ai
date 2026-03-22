#!/usr/bin/env python3
"""
Dice AI Job Search - Flask API
"""
from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS

from models import db
from routes.chat import chat_bp

load_dotenv()

app = Flask(__name__)
CORS(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///dice_ai.db"
db.init_app(app)

app.register_blueprint(chat_bp)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
