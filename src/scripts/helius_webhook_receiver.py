from flask import Flask, request, jsonify
from termcolor import cprint
import json
from pathlib import Path
from datetime import datetime
from pyngrok import ngrok

app = Flask(__name__)

# Create data directory
data_dir = Path("moondev/src/data/webhook_data")
data_dir.mkdir(parents=True, exist_ok=True)

# Configure ngrok with auth token
ngrok.set_auth_token("2JIlm3Bci4fzHbVJ9JPALTKLz9r_7jntgnAmWpJ6B49J9FAdh")

# Connect to your specific domain
tunnel_config = ngrok.connect(5000, domain="blessed-airedale-electric.ngrok-free.app")
cprint(f"\n🌐 Public Webhook URL: {tunnel_config.public_url}/webhook\n", "green")

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # Verify auth header
        auth_header = request.headers.get('Authorization')
        expected_auth = 'Bearer moondev-helius-token-mint'
        
        if not auth_header or auth_header != expected_auth:
            cprint("🚫 Unauthorized webhook attempt", "red")
            return jsonify({"status": "unauthorized"}), 401

        # Process webhook data
        data = request.json
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save data
        filename = f"{timestamp}_webhook.json"
        with open(data_dir / filename, 'w') as f:
            json.dump(data, f, indent=2)
            
        cprint(f"📥 Received webhook data", "green")
        return {"status": "success"}, 200
        
    except Exception as e:
        cprint(f"❌ Error: {str(e)}", "red")
        return {"status": "error"}, 500

if __name__ == '__main__':
    cprint("\n🚀 Starting Moon Dev's Helius Webhook Receiver...", "cyan")
    cprint("📂 Saving transactions to: " + str(data_dir), "yellow")
    cprint("🔍 Health check endpoint: http://localhost:5000/health\n", "magenta")

    app.run(host='0.0.0.0', port=5000)
