import jwt
import datetime
import os
from flask import Flask, request, jsonify
from flask_mysqldb import MySQL
from werkzeug.security import check_password_hash

# Initialize Flask app
server = Flask(__name__)
mysql = MySQL(server)

# Configuration from environment variables
server.config["MYSQL_HOST"] = os.environ.get("MYSQL_HOST")
server.config["MYSQL_USER"] = os.environ.get("MYSQL_USER")
server.config["MYSQL_PASSWORD"] = os.environ.get("MYSQL_PASSWORD")
server.config["MYSQL_DB"] = os.environ.get("MYSQL_DB")
server.config["MYSQL_PORT"] = int(os.environ.get("MYSQL_PORT", 3306))  # default port 3306

# Route: Login and generate JWT token
@server.route("/login", methods=["POST"])
def login():
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return jsonify({"error": "Missing credentials"}), 401

    # Check DB for matching user
    cur = mysql.connection.cursor()
    result = cur.execute(
        "SELECT email, password FROM user WHERE email=%s", (auth.username,)
    )

    if result > 0:
        email, hashed_password = cur.fetchone()

        # Verify password using bcrypt hash
        if not check_password_hash(hashed_password, auth.password):
            return jsonify({"error": "Invalid credentials"}), 401

        # Create and return JWT token
        token = create_jwt(email, os.environ.get("JWT_SECRET"), True)
        return jsonify({"token": token}), 200

    return jsonify({"error": "Invalid credentials"}), 401

# Helper function: Create JWT
def create_jwt(username, secret, is_admin):
    payload = {
        "username": username,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1),
        "iat": datetime.datetime.utcnow(),
        "admin": is_admin,
    }
    return jwt.encode(payload, secret, algorithm="HS256")

# Route: Validate JWT token
@server.route("/validate", methods=["POST"])
def validate():
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        return jsonify({"error": "Missing Authorization header"}), 401

    try:
        token = auth_header.split(" ")[1]
        decoded = jwt.decode(token, os.environ.get("JWT_SECRET"), algorithms=["HS256"])
        return jsonify(decoded), 200
    except IndexError:
        return jsonify({"error": "Invalid Authorization header format"}), 400
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 403

# Run the server
if __name__ == "__main__":
    server.run(host="0.0.0.0", port=5000)
