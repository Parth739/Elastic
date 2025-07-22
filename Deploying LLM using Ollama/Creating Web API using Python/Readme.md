### 1. Connect to your E2E instance
ssh ubuntu@103.123.45.67  # Replace with your IP

### 2. Create a directory for your project
mkdir ollama-api
cd ollama-api

### 3. Create the API server file
cat > api_server.py << 'EOF'

### 4. Install dependencies
pip3 install flask flask-cors requests

### 5. Make sure Ollama is running
ollama serve &

### 6. Run 
python3 api_server.py
