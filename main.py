from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import zipfile
import os
import json
import shutil


app = Flask(__name__)
index_of_question=0
action={
    'action':'',
}
quizName = ''
display_bool = False

# Configuration
UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = {'zip'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return jsonify({'message': 'Welcome to the Quiz Upload API'}), 200

@app.route('/update-display', methods=['POST'])
def update_display():
    global quizName, index_of_question, display_bool
    data = request.get_json()
    if not data or 'quizName' not in data:
        return jsonify({'error': 'Invalid input, "quizName" key is required'}), 400
    quizName = data['quizName']
    index_of_question = 0
    display_bool = True
    return jsonify({'message': 'Quiz name updated successfully', 'quizName': quizName}), 200

@app.route('/display', methods=['GET'])
def display_quiz():
    global quizName
    if not quizName:
        return jsonify({'quizName':'none','display':False}), 200
    return jsonify({'quizName': quizName, 'display': display_bool}), 200

@app.route('/update-action', methods=['POST'])
def update_action():
    global action, index_of_question, display_bool  # Declare both at the top
    data = request.get_json()
    if not data or 'action' not in data:
        return jsonify({'error': 'Invalid input, "action" key is required'}), 400
    action['action'] = data['action']
    if action['action']=='NEXT':
        index_of_question += 1
    elif action['action']=='PREVIOUS':
        if index_of_question > 0:
            index_of_question -= 1
    elif action['action']=='FINISH':
        display_bool = False
    return jsonify({'message': 'Action updated successfully', 'action': action}), 200

@app.route('/action', methods=['GET'])
def to_show():
    return jsonify(action), 200

@app.route('/live-quiz/<chapter_name>', methods=['GET'])
def to_show_quiz(chapter_name):
    folder_path = os.path.join('./uploads', chapter_name)
    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        return jsonify({'error': f'Folder "{chapter_name}" not found'}), 404
    questions_json_path = os.path.join(folder_path, 'questions.json')
    if not os.path.isfile(questions_json_path):
        return jsonify({'error': f'"questions.json" not found in "{chapter_name}"'}), 404

    with open(questions_json_path, 'r', encoding='utf-8') as f:
        questions_data = json.load(f)
    question=questions_data['questions']
    return jsonify({'question': question[index_of_question], 'display': display_bool}), 200

@app.route('/quiz-upload', methods=['POST'])
def upload_quiz_zip():
    # Check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    # If user does not select file, browser submits empty part
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        temp_dir = './uploads'
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            # Save the zip file temporarily
            zip_path = os.path.join(temp_dir, filename)
            file.save(zip_path)
            
            # Process the zip file
            result = process_quiz_zip(zip_path, temp_dir)
            
            return jsonify({
                'message': 'File successfully uploaded and processed',
                'details': result
            }), 200
            
        except zipfile.BadZipFile:
            return jsonify({'error': 'Invalid zip file'}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            if os.path.exists(zip_path):
                os.remove(zip_path)
    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/quizzes',methods=['GET'])
def display_extracted_zip():
    folder_path ='./uploads'
    if not folder_path:
        return jsonify({'error': 'Missing folder path'}), 400

    folder_path = os.path.abspath(folder_path)
    if not os.path.exists(folder_path):
        app.logger.error(f"Provided folder path does not exist: {folder_path}")
        return jsonify({'error': 'Invalid folder path'}), 400

    extracted_files = []

    try:
        for root, dirs, files in os.walk(folder_path):
            for dir in dirs:
                file_path = dir
                questions_json_path = os.path.join(folder_path, dir, 'questions.json')
                if os.path.isfile(questions_json_path):
                    try:
                        with open(questions_json_path, 'r', encoding='utf-8') as f:
                            questions_data = json.load(f)
                            quiz_data=questions_data['quiz']
                        extracted_files.append(quiz_data)
                    except Exception as e:
                        extracted_files.append({
                            'quiz_name': dir,
                            'error': f'Failed to load questions.json: {str(e)}'
                        })

        return jsonify(extracted_files), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/chapter/<chapter_name>', methods=['GET'])
def get_chapter_zip(chapter_name):
    folder_path = os.path.join('./uploads', chapter_name)
    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        return jsonify({'error': f'Folder "{chapter_name}" not found'}), 404

    zip_file_path = os.path.join('./uploads', f"{chapter_name}.zip")
    try:
        # Create a zip of the folder, including the folder itself as the root
        with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    abs_path = os.path.join(root, file)
                    # Include the chapter folder as the root in the zip
                    rel_path = os.path.relpath(abs_path, os.path.dirname(folder_path))
                    zipf.write(abs_path, arcname=rel_path)
        file_size = os.path.getsize(zip_file_path)
        response = send_file(zip_file_path, as_attachment=True)
        response.headers['Content-Length'] = file_size
        return response
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if os.path.exists(zip_file_path):
            os.remove(zip_file_path)

@app.route('/quiz-delete/<quiz_name>', methods=['DELETE','POST'])
def delete_quiz(quiz_name):
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], quiz_name)
    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        return jsonify({'error': f'Quiz "{quiz_name}" not found'}), 404

    try:
        # Remove the quiz folder and all its contents
        shutil.rmtree(folder_path)
        return jsonify({'message': f'Quiz "{quiz_name}" deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def process_quiz_zip(zip_path, extract_dir):
    """Process the quiz zip file and extract its contents"""
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # Extract all files
        zip_ref.extractall(extract_dir)
        
        # Look for specific files in the zip
        extracted_files = zip_ref.namelist()
        
        result = {
            'files': extracted_files,
            'questions': [],
            'media_files': []
        }
        
  
        return result

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(host='0.0.0.0',port=5000)
