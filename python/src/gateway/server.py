import os
import json
import gridfs
import pika
from flask import Flask, request, send_file, jsonify
from flask_pymongo import PyMongo
from bson.objectid import ObjectId

from auth import validate
from auth_svc import access
from storage import util

# ----------------------------
# App Initialization
# ----------------------------

server = Flask(__name__)

# MongoDB connections
server.config["MONGO_URI_VIDEO"] = "mongodb://host.minikube.internal:27017/videos"
server.config["MONGO_URI_MP3"] = "mongodb://host.minikube.internal:27017/mp3s"

mongo_video = PyMongo(server, uri=server.config["MONGO_URI_VIDEO"])
mongo_mp3 = PyMongo(server, uri=server.config["MONGO_URI_MP3"])

# GridFS for file storage
fs_videos = gridfs.GridFS(mongo_video.db)
fs_mp3s = gridfs.GridFS(mongo_mp3.db)

# RabbitMQ connection setup
try:
    connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq"))
    channel = connection.channel()
except Exception as e:
    print(f"Error connecting to RabbitMQ: {e}")
    channel = None


# ----------------------------
# Routes
# ----------------------------

@server.route("/login", methods=["POST"])
def login():
    """User login: returns a JWT token on successful authentication."""
    token, err = access.login(request)

    return token if not err else (err, 401)


@server.route("/upload", methods=["POST"])
def upload():
    """Uploads a video file to MongoDB (GridFS) and sends a message to RabbitMQ for processing."""
    token_data, err = validate.token(request)
    if err:
        return err

    user = json.loads(token_data)

    if not user.get("admin"):
        return jsonify({"error": "Not authorized"}), 401

    if len(request.files) != 1:
        return jsonify({"error": "Exactly 1 file is required"}), 400

    uploaded_file = next(iter(request.files.values()))

    upload_error = util.upload(uploaded_file, fs_videos, channel, user)
    if upload_error:
        return upload_error

    return jsonify({"message": "Upload successful"}), 200


@server.route("/download", methods=["GET"])
def download():
    """Downloads an MP3 file from MongoDB (GridFS) by file ID."""
    token_data, err = validate.token(request)
    if err:
        return err

    user = json.loads(token_data)

    if not user.get("admin"):
        return jsonify({"error": "Not authorized"}), 401

    fid = request.args.get("fid")
    if not fid:
        return jsonify({"error": "Missing 'fid' parameter"}), 400

    try:
        file_data = fs_mp3s.get(ObjectId(fid))
        return send_file(file_data, download_name=f"{fid}.mp3")
    except Exception as e:
        print(f"Download error: {e}")
        return jsonify({"error": "Internal server error"}), 500


# ----------------------------
# Main Application Entry
# ----------------------------

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8080, debug=False)
