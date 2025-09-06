import os
import shutil
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import subprocess
import sys

app = Flask(__name__, static_folder="frontend/build", static_url_path="/")
CORS(app)

FLAMES = {
    'F': 'Friend',
    'L': 'Love',
    'A': 'Admire',
    'M': 'Marriage',
    'E': 'Enemy',
    'S': 'Secret Lover'
}

def flames_result(name1: str, name2: str) -> dict:
    if name1 is None: name1 = ""
    if name2 is None: name2 = ""

    a = [c.lower() for c in name1 if c.isalpha()]
    b = [c.lower() for c in name2 if c.isalpha()]

    for ch in a[:]:
        if ch in b:
            a.remove(ch)
            b.remove(ch)

    remaining_count = len(a) + len(b)
    if remaining_count == 0:
        return {'key': 'S', 'meaning': FLAMES['S'], 'count': 0}

    sequence = list(FLAMES.keys())
    current_index = 0
    while len(sequence) > 1:
        remove_index = (current_index + remaining_count - 1) % len(sequence)
        sequence.pop(remove_index)
        current_index = remove_index % len(sequence)
    final_key = sequence[0]
    return {'key': final_key, 'meaning': FLAMES[final_key], 'count': remaining_count}

def advice_for(key):
    return {
        'F': "Be a great friend first — friendships can grow into something more.",
        'L': "Love is glowing — small, consistent gestures will help it grow.",
        'A': "Admiration is sweet — a genuine compliment might spark something.",
        'M': "Long-term vibes — think meaningful promises, not haste.",
        'E': "There might be friction — approach gently and seek understanding.",
        'S': "Secret lover — feelings are private. Consider being brave but respectful."
    }.get(key, "")

@app.route("/api/calculate", methods=["POST"])
def calculate():
    try:
        data = request.get_json() or {}
    except Exception:
        data = {}
    name1 = data.get("name1", "")
    name2 = data.get("name2", "")
    if not isinstance(name1, str) or not isinstance(name2, str):
        return jsonify({"error": "Invalid input, names must be strings."}), 400
    result = flames_result(name1, name2)
    ui = {
        "emoji": {
            'F': '😊','L': '❤️','A': '😍','M': '💍','E': '😤','S': '😉'
        }.get(result['key'], '💞'),
        "advice": advice_for(result['key'])
    }
    payload = {**result, **ui}
    return jsonify(payload), 200

# Serve static React build if present. If not present, return a helpful HTML that
# tells user how to build or offers a quick dev fallback.
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    build_folder = app.static_folder
    index_path = os.path.join(build_folder, "index.html")

    # Serve static file if exists
    if path != "" and os.path.exists(os.path.join(build_folder, path)):
        return send_from_directory(build_folder, path)

    # If build exists serve index.html
    if os.path.exists(index_path):
        return send_from_directory(build_folder, "index.html")

    # Helpful fallback HTML (no raw "frontend not found" — user-friendly)
    fallback = """
    <!doctype html>
    <html>
      <head><meta charset="utf-8"><title>Kamzy's Love Calculator</title></head>
      <body style="font-family:Arial,Helvetica,sans-serif; text-align:center; padding:40px;">
        <h2>Frontend build not found</h2>
        <p>To run locally, build the React frontend first.</p>
        <pre style="background:#f6f6f6; padding:12px; display:inline-block; text-align:left;">
cd frontend
npm install
npm run build
cd ..
python app.py
        </pre>
        <p>Or run React dev server separately (for development):</p>
        <pre style="background:#f6f6f6; padding:12px; display:inline-block; text-align:left;">
cd frontend
npm install
npm start
# then in another terminal:
flask run
        </pre>
        <p style="color:#555">When deployed on Render this step is automatic — Render builds the frontend for you.</p>
      </body>
    </html>
    """
    return fallback, 200

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Route not found", "message": "🥺 Love got lost. Use the calculator at /"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Server error", "message": "😵 Something went wrong. Try again later."}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    # Optional helpful auto-build on local start:
    # If the frontend/build is missing and npm is available, attempt to build once.
    build_dir = os.path.join("frontend", "build")
    if not os.path.exists(build_dir):
        npm = shutil.which("npm")
        if npm:
            print("frontend/build not found — attempting local npm install & build (may take time)...", file=sys.stderr)
            try:
                subprocess.check_call(["npm", "install"], cwd="frontend")
                subprocess.check_call(["npm", "run", "build"], cwd="frontend")
                print("Frontend built successfully.", file=sys.stderr)
            except subprocess.CalledProcessError:
                print("Automatic build failed. Please run 'cd frontend && npm install && npm run build' manually.", file=sys.stderr)
        else:
            print("npm not found — frontend build missing. See / page for instructions.", file=sys.stderr)
    app.run(host="0.0.0.0", port=port, debug=False)
