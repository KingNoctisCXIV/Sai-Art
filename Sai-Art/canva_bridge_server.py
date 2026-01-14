"""
Simple Flask-based bridge service for Canva Connect API.

This script demonstrates how to accept structured requests from your GPT
and use your stored access token to call Canva Connect API endpoints.
The example includes two endpoints:

1. POST /designs
   Creates a new design from a template and returns the design ID and
   shareable URL.

2. POST /designs/<design_id>/export
   Exports a design to a specified format and returns a link to the
   exported file.

Before running this script, set the CANVA_ACCESS_TOKEN environment variable
with your Canva access token (obtained via OAuth).

Run the server locally:

    export CANVA_ACCESS_TOKEN=your_token_here
    python canva_bridge_server.py

Then the server will listen on port 8000 by default.

Note: This is a minimal example and does not include error handling or
input validation. Customize it to suit your needs and security
requirements.
"""

import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

CANVA_BASE_URL = "https://api.canva.com/rest/v1"
ACCESS_TOKEN = os.environ.get("CANVA_ACCESS_TOKEN")

if not ACCESS_TOKEN:
    raise RuntimeError("Please set the CANVA_ACCESS_TOKEN environment variable")

def canva_request(method: str, path: str, **kwargs):
    """Helper function to call the Canva Connect API with the access token."""
    headers = kwargs.pop("headers", {})
    headers.setdefault("Authorization", f"Bearer {ACCESS_TOKEN}")
    headers.setdefault("Content-Type", "application/json")
    url = f"{CANVA_BASE_URL}{path}"
    response = requests.request(method, url, headers=headers, **kwargs)
    response.raise_for_status()
    return response.json()

@app.route("/designs", methods=["POST"])
def create_design():
    data = request.json or {}
    template_id = data.get("template_id")
    if not template_id:
        return jsonify({"error": "template_id is required"}), 400
    title = data.get("title", "Untitled Design")
    # This payload matches Canva's create design API; adjust fields as needed.
    payload = {
        "template_id": template_id,
        "title": title,
        # Additional fields like document_settings, pages, etc. could go here.
    }
    result = canva_request("POST", "/designs", json=payload)
    # The API response contains the design ID and share URL.
    return jsonify({
        "design_id": result.get("id"),
        "design_url": result.get("share_url"),
    })

@app.route("/designs/<design_id>/export", methods=["POST"])
def export_design(design_id):
    data = request.json or {}
    export_format = data.get("format", "png")
    payload = {
        "file_format": export_format
    }
    result = canva_request("POST", f"/designs/{design_id}/exports", json=payload)
    export_url = result.get("url")
    if not export_url:
        urls = result.get("urls")
        if isinstance(urls, list) and urls:
            export_url = urls[0]
    if not export_url:
        export_url = result.get("export_url")
    return jsonify({
        "export_url": export_url,
    })

if __name__ == "__main__":
    # Use 0.0.0.0 to allow external connections if deploying; otherwise localhost.
    app.run(host="0.0.0.0", port=8000)
