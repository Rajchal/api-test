from flask import Flask, request, jsonify, render_template
import os

app = Flask(__name__)

# Allow CORS for mobile access
from flask_cors import CORS
CORS(app)

# Store the current question
current_question = "Welcome! Waiting for the first question..."

# Store student answers (mock data, replace with a database)
student_answers = {
    "student-1": "A",
    "student-2": "B",
    "student-3": "C"
}

@app.route('/')
def home():
    """Home page showing the current question"""
    return render_template('index.html', question=current_question)

@app.route('/display')
def display_question():
    """Page for students to see the latest question"""
    
    return current_question.replace(',','<br />')

@app.route('/answers')
def display_answers():
    return student_answers

# Endpoint to receive commands from mobile
@app.route('/command', methods=['POST'])
def receive_command():
    global current_question
    global student_answers

    data = request.get_json()
    if not data or 'action' not in data:
        return jsonify({"error": "Invalid request"}), 400

    action = data['action']

    # Change the displayed question
    if action == "change_question":
        current_question = data.get('question', 'No question provided')
        print(f"Changing question to: {current_question}")
        return jsonify({"status": "Question updated", "question": current_question})

    # View student answers
    elif action == "view_answers":
        return jsonify({"status": "Success", "answers": student_answers})

    # Restart Raspberry Pi
    elif action == "restart":
        os.system("sudo reboot")  
        return jsonify({"status": "Raspberry Pi is restarting..."})
    elif  action == "button_pressed":
        button = data.get('button', 'Unknown')
        student = button.split(',')
        but=student[0]
        stu=student[1]
        student_answers[stu]=but
        print(f"Button {but} pressed by student {stu}")
        return jsonify({"status": "Button received", "button": button})
    else:
        return jsonify({"error": "Unknown command"}), 400

# Run API on local network
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
