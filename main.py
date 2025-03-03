from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit
import json

app = Flask(__name__)
socketio = SocketIO(app)

# Store the questions, student answers, and current question index
questions_data = {}
student_answers = []
current_question_index = 0

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


# GET request to get all answers submitted by students
@app.route('/get_answers', methods=['GET'])
def get_answers():
    try:
        # Return all submitted answers
        return jsonify({"student_answers": student_answers}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_chapters',methods=['GET'])
def get_chapters():
    try:
        return questions_data
    except Exception as e:
        return jsonify({"error":str(e)}),500
# Render the webpage to show questions and answers
@app.route('/')
def index():
    return  questions_data
@app.route('/ans')
def ans():
    return student_answers

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
    app.run(debug=True, host='0.0.0.0', port=5000)

