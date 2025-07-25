# Testing LLMs Using Ollama + HTTPS Setup with Nginx
For Testing cases We can Use Ollama To deploy and Test LLMs easily via GPU or our local machine

1] Download Ollama
```
curl -fsSL https://ollama.com/install.sh | sh
```

2]Download the LLM 
```
ollama pull deepseek-r1:32b-qwen-distill-q4_K_M
```

3]set up HTTPS for your Ollama API
#### Step 1: Install Nginx

install Nginx on your server:

```bash
# Update package list
sudo apt update

# Install Nginx
sudo apt install nginx -y

# Start and enable Nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Verify Nginx is running
sudo systemctl status nginx
```

#### Step 2: Verify Nginx Installation

After installation, check if Nginx is working:

```bash
# Check if Nginx directories exist now
ls -la /etc/nginx/

# Test Nginx by accessing your server IP in a browser
curl http://localhost
```

#### Step 3: Configure Firewall

Allow Nginx through the firewall:

```bash
# Allow Nginx Full (both HTTP and HTTPS)
sudo ufw allow 'Nginx Full'

# Allow SSH if not already allowed
sudo ufw allow OpenSSH

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

#### Step 4: Create Nginx Configuration for Ollama

Now create the configuration for your domain:

```bash
# Create configuration file
sudo nano /etc/nginx/sites-available/llm-be.infollion.ai
```

Add this configuration:

```nginx
server {
    listen 80;
    server_name domain-name;

    location / {
        proxy_pass http://127.0.0.1:11434;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support for streaming responses
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Increase timeout for long LLM requests
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
        client_max_body_size 50M;
    }
}
```

#### Step 5: Enable the Site

```bash
# Remove default site (optional)
sudo rm /etc/nginx/sites-enabled/default

# Enable your site
sudo ln -s /etc/nginx/sites-available/llm-be.infollion.ai /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

#### Step 6: Install Certbot

Now install Certbot for SSL certificates:

```bash
# Install Certbot and Nginx plugin
sudo apt install certbot python3-certbot-nginx -y
```

#### Step 7: Ensure Ollama is Running

Before getting the certificate, make sure Ollama is running:

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running, start it
ollama serve
```
#### Step 8: Obtain SSL Certificate

```bash
# Make sure your domain points to your server's IP first!
# Then run Certbot
sudo certbot --nginx -d llm-be.infollion.ai
```


#### Step 9: Testing

```bash
# Test the HTTPS endpoint
curl https://llm-be.infollion.ai/api/tags

# Test a generation request
curl https://llm-be.infollion.ai/api/generate -d '{
  "model": "llama3.1:8b-instruct-fp16",
  "prompt": "Hello, how are you?",
  "stream": false
}'
```
