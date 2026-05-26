"""
Intentionally vulnerable endpoint to trigger CodeQL path-traversal detection.
DO NOT deploy this code — it exists solely for security-scanning validation.
"""

import os
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename

vulnerable_bp = Blueprint("vulnerable", __name__)


@vulnerable_bp.route("/read-file", methods=["POST"])
def read_file():
    """
    Reads a file requested by the client, constrained to a safe directory.
    """
    body = request.get_json(force=True)
    if not isinstance(body, dict):
        return jsonify({"error": "invalid request body"}), 400

    file_path = body.get("path", "")
    if not isinstance(file_path, str) or not file_path:
        return jsonify({"error": "invalid path"}), 400
    if os.path.isabs(file_path):
        return jsonify({"error": "invalid path"}), 400

    safe_name = secure_filename(file_path)
    if not safe_name or safe_name != file_path:
        return jsonify({"error": "invalid path"}), 400

    base_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), "safe_files"))
    normalized_candidate = os.path.normpath(os.path.join(base_dir, safe_name))
    candidate_path = os.path.realpath(normalized_candidate)

    if os.path.commonpath([base_dir, candidate_path]) != base_dir:
        return jsonify({"error": "invalid path"}), 400

    with open(candidate_path, "r", encoding="utf-8") as f:
        content = f.read()

    return jsonify({"content": content})
