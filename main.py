from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# Allow CORS (for mobile app access)
from flask_cors import CORS
CORS(app)

@app.route('/')
def home():
    return jsonify({"message": "Raspberry Pi API is running!"})

# Endpoint to receive commands from mobile
@app.route('/command', methods=['POST'])
def receive_command():
    data = request.get_json()

    if not data or 'action' not in data:
        return jsonify({"error": "Invalid request"}), 400

    action = data['action']
    
    # Example: Change questions on the projector
    if action == "change_question":
        question = data.get('question', 'No question provided')
        print(f"Changing question to: {question}")
        return jsonify({"status": "Question updated", "question": question})

    # Example: View answers
    elif action == "view_answers":
        answers = {"student1": "A", "student2": "B", "student3": "C"}  # Example data
        return jsonify({"status": "Success", "answers": answers})

    # Example: Restart the Raspberry Pi
    elif action == "restart":
        os.system("sudo reboot")  # ⚠️ Only use if you need to reboot the Pi
        return jsonify({"status": "Raspberry Pi is restarting..."})

    else:
        return jsonify({"error": "Unknown command"}), 400

# Run API on local network
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
