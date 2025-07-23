# Install Ollama (one command)
curl -fsSL https://ollama.com/install.sh | sh

# Pull and run Llama 3.1 8B (this downloads ~4.7GB)
ollama pull llama3.1:8b
## ollama pull llama3.1:8b-instruct-fp16
ollama run llama3.1:8b
## ollama run llama3.1:8b-instruct-fp16

# In another terminal, run the API server
ollama serve

# Test the API
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.1:8b",
  "prompt": "Why is the sky blue?"
}'


# For creating api to access from other machines
# Stop Ollama if running
sudo systemctl stop ollama

# Set Ollama to listen on all interfaces
export OLLAMA_HOST=0.0.0.0:11434

# Start Ollama
ollama serve

# Allow port 11434 through firewall
sudo ufw allow 11434/tcp

# Get public IP
curl ifconfig.me

# Test from another machine
curl http://YOUR_E2E_PUBLIC_IP:11434/api/generate -d '{
  "model": "llama3.1:8b",
  "prompt": "Hello world",
  "stream": false
}'


