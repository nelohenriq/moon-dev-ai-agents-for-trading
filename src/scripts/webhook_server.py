
from flask import Flask, request, jsonify
from termcolor import cprint
import json
from pathlib import Path
from datetime import datetime

app = Flask(__name__)


# Create data directory
data_dir = Path("src/data/webhook_data")
data_dir.mkdir(parents=True, exist_ok=True)

@app.route('/webhook/helius', methods=['POST'])
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

    app.run(port=5000)
