# save as api_server.py
from flask import Flask, request, jsonify
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS 

OLLAMA_URL = "http://localhost:11434/api/generate"

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    prompt = data.get('prompt', '')
    
    # Call Ollama
    response = requests.post(OLLAMA_URL, json={
        "model": "llama3.1:8b",
        "prompt": prompt,
        "stream": False
    })
    
    return jsonify({
        "response": response.json()['response'],
        "model": "llama3.1:8b"
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
