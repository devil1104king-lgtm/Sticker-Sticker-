from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    """Health check endpoint for Render/VPS."""
    return jsonify({
        "status": "online",
        "service": "Sticker Sticker Game Bot",
        "version": "1.0.0"
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
  
