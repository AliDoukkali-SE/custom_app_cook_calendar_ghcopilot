"""
Intentionally vulnerable endpoint to trigger CodeQL path-traversal detection.
DO NOT deploy this code — it exists solely for security-scanning validation.
"""

import os
from flask import Blueprint, request, jsonify

vulnerable_bp = Blueprint("vulnerable", __name__)


@vulnerable_bp.route("/read-file", methods=["POST"])
def read_file():
    """
    Reads a file requested by the client, constrained to a safe directory.
    """
    body = request.get_json(force=True)
    file_path = body.get("path", "")

    base_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), "safe_files"))
    candidate_path = os.path.realpath(os.path.join(base_dir, file_path))

    if os.path.commonpath([base_dir, candidate_path]) != base_dir:
        return jsonify({"error": "invalid path"}), 400

    with open(candidate_path, "r") as f:
        content = f.read()

    return jsonify({"content": content})
