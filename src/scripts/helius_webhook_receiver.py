"""
🌙 Moon Dev's Helius Webhook Receiver

Receives and processes Solana transaction webhooks from Helius.
Built with love by Moon Dev 🚀
"""

from flask import Flask, request, jsonify
from termcolor import cprint
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from pyngrok import ngrok, conf
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Create data directory if it doesn't exist
data_dir = Path("src/data/webhook_data")
data_dir.mkdir(parents=True, exist_ok=True)

# Add your ngrok auth token
ngrok.set_auth_token("2JIlm3Bci4fzHbVJ9JPALTKLz9r_7jntgnAmWpJ6B49J9FAdh")

# Start ngrok
public_url = ngrok.connect(5000)
cprint(f"\n🌐 Public Webhook URL: {public_url}/webhook/helius\n", "green")
@app.route('/webhook/helius', methods=['POST'])
def helius_webhook():
    try:
        # Verify the auth header
        auth_header = request.headers.get('Authorization')
        expected_auth = 'Bearer moondev-helius-token-mint'  # Match this with your Helius config
        
        if not auth_header or auth_header != expected_auth:
            cprint("🚫 Unauthorized webhook attempt", "red")
            return jsonify({"status": "unauthorized"}), 401
        # Get the webhook payload
        payload = request.json
        
        # Generate timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        tx_id = payload.get('signature', 'no_signature')[:8]
        
        # Save transaction data
        filename = f"{timestamp}_{tx_id}.json"
        with open(data_dir / filename, 'w') as f:
            json.dump(payload, f, indent=2)
        
        # Print nice console output
        cprint(f"📥 Received transaction: {tx_id}", "green")
        cprint(f"📁 Saved to: {filename}", "cyan")
        
        return jsonify({
            "status": "success",
            "message": "Transaction received and saved",
            "tx_id": tx_id
        }), 200

    except Exception as e:
        cprint(f"❌ Error processing webhook: {str(e)}", "red")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    cprint("\n🚀 Starting Moon Dev's Helius Webhook Receiver...", "cyan")
    cprint("📂 Saving transactions to: " + str(data_dir), "yellow")
    cprint("🔍 Health check endpoint: http://localhost:5000/health\n", "magenta")
    
    app.run(host='0.0.0.0', port=5001)
