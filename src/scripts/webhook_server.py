from flask import Flask, request
import json

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    # Process the webhook data here
    print(f"Received webhook: {json.dumps(data, indent=2)}")
    return {"status": "success"}, 200

if __name__ == '__main__':
    app.run(port=5000, debug=True)
