"""
Intentionally vulnerable endpoint to trigger CodeQL path-traversal detection.
DO NOT deploy this code — it exists solely for security-scanning validation.
"""

from flask import Blueprint, request, jsonify

vulnerable_bp = Blueprint("vulnerable", __name__)


@vulnerable_bp.route("/read-file", methods=["POST"])
def read_file():
    """
    BAD: opens a file whose path comes directly from user input
    without any sanitization or validation — classic path traversal.
    """
    body = request.get_json(force=True)
    file_path = body.get("path", "")

    # No validation — an attacker can supply "../../etc/passwd"
    with open(file_path, "r") as f:
        content = f.read()

    return jsonify({"content": content})
