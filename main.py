from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit
import socket

app = Flask(__name__)
socketio = SocketIO(app)

# Store the questions, student answers, and current question index
questions_data = {
            "question":"what is apple",
            "options":[
                    "honey",
                    "veggies",
                    "fruit",
                    "pumpkin"
                ],
            "show":"yes",
            "correct":"2",
        }
student_answers = []
commands={
        "next":"true"
        }

#check commands if they are updated by raspberry pi
@app.route('/commands', methods=['GET'])
def get_commands():
    @socketio.on('get_commands')
    def handle_get_commands():
        emit('commands', commands)
    return jsonify(commands), 200



# POST request to receive questions and options from teacher
@app.route('/upload_questions', methods=['POST'])
def upload_questions():
    global current_question_index
    try:
        # Receive JSON from teacher
        data = request.get_json()

        # Validate if data contains chapter and questions
        if 'chapter' not in data or 'questions' not in data:
            return jsonify({"error": "Invalid data format"}), 400
        chapter_name = data['chapter']
        questions = data['questions']

        # Store questions in a dictionary
        questions_data[chapter_name] = questions
        current_question_index = 0  # Reset to the first question

        # Emit the first question to all connected clients
        socketio.emit('new_question', questions_data[chapter_name][current_question_index])

        return jsonify({"message": f"Questions for {chapter_name} added successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# POST request to receive answers from students (via ESP8266 remote)
@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    global current_question_index
    try:
        # Get answer data from ESP8266 (button press)

        data = request.get_json()

        # Validate answer data
        if 'student_id' not in data or 'question_id' not in data or 'answer' not in data:
            return jsonify({"error": "Invalid answer data"}), 400

        student_id = data['student_id']
        question_id = data['question_id']
        answer = data['answer']

        # Save the student's answer
        student_answers.append({
            "student_id": student_id,
            "question_id": question_id,
            "answer": answer
        })

        # Check if we need to move to the next question
        if question_id == current_question_index:
            current_question_index += 1

            # If there are more questions, emit the next question
            if current_question_index < len(questions_data[list(questions_data.keys())[0]]):
                socketio.emit('new_question', questions_data[list(questions_data.keys())[0]][current_question_index])

        return jsonify({"message": "Answer submitted successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/get_chapters',methods=['GET'])
def get_chapters():
    try:
        return ques
    except Exception as e:
        return jsonify({"error":str(e)}),500
# Render the webpage to show questions and answers
@app.route('/questions-live')
def index():
    return  questions_data

@app.route('/answers')
def display_answers():
    return student_answers


# Run API on local network
if __name__ == '__main__':
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(f"Server is running on IP: {local_ip}")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)

