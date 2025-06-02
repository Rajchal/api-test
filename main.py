from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import zipfile
import os
import json
import shutil
from flask_cors import CORS


app = Flask(__name__)
CORS(app)
index_of_question=0
action={
    'action':'',
}
scores={
    'Nidhi':0,
    'Sachet':0,
    'Anjal':0
}
flag={
    'Nidhi':True,
    'Sachet':True,
    'Anjal':True
}
quizName = ''
display_bool = False
global_question=[]
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
    global action, index_of_question, display_bool, flag  # Declare both at the top
    data = request.get_json()
    if not data or 'action' not in data:
        return jsonify({'error': 'Invalid input, "action" key is required'}), 400
    action['action'] = data['action']
    if action['action']=='NEXT':
        index_of_question += 1
        flag['Anjal']=True
        flag['Nidhi']=True
        flag['Sachet']=True
    elif action['action']=='PREVIOUS':
        if index_of_question > 0:
            index_of_question -= 1
    elif action['action']=='FINISH':
        display_bool = False
        global_question.clear()
        index_of_question = 0
        flag['Anjal']=True
        flag['Nidhi']=True
        flag['Sachet']=True   
    elif action['action']=='EXIT':
        display_bool = False
        index_of_question = 0
        action['action'] = ''
        global_question.clear()
        flag['Anjal']=True
        flag['Nidhi']=True
        flag['Sachet']=True        
    return jsonify({'message': 'Action updated successfully', 'action': action}), 200

@app.route('/action', methods=['GET'])
def to_show():
    return jsonify(action), 200

@app.route('/live-quiz/<chapter_name>', methods=['GET'])
def to_show_quiz(chapter_name):
    global global_question
    folder_path = os.path.join('./uploads', chapter_name)
    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        return jsonify({'error': f'Folder "{chapter_name}" not found'}), 404
    questions_json_path = os.path.join(folder_path, 'questions.json')
    if not os.path.isfile(questions_json_path):
        return jsonify({'error': f'"questions.json" not found in "{chapter_name}"'}), 404

    with open(questions_json_path, 'r', encoding='utf-8') as f:
        questions_data = json.load(f)
    global_question=questions_data['questions']
    return jsonify({'question': global_question[index_of_question], 'display': display_bool}), 200

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

@app.route('/answer', methods=['POST'])
def submit_answer():
    global flag
    data = request.get_json()
    if not data or 'button' not in data:
        return jsonify({'error': 'Invalid input, "button" key is required'}), 400
    
    answer = data['button']
    student =data['student']

    quest=global_question[index_of_question]

    if int(answer)== quest['correctOptionIndex'] and flag[student]:
        scores[student]+=1
        flag[student]==False

    return jsonify({'status': 'success', 'answer': answer,'student':student}), 200

@app.route('/scores',methods=['GET'])
def get_scores():
    return jsonify(scores), 200

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or 'user_id' not in data or 'password' not in data or 'role' not in data:
        return jsonify({'error': 'Invalid input, "username", "password" and "role" keys are required'}), 400

    username = data['user_id']
    password = data['password']
    role = data['role']
    
    # Check credentials from userpass.json file
    userpass_path = os.path.join(os.path.dirname(__file__), 'userpass.json')
    if not os.path.isfile(userpass_path):
        return jsonify({'error': 'User credentials file not found'}), 500

    try:
        with open(userpass_path, 'r', encoding='utf-8') as f:
            users = json.load(f)
    except Exception as e:
        return jsonify({'error': f'Failed to read credentials: {str(e)}'}), 500

    # users should be a dict: { "username1": {"password": "...", "role": "..."}, ... }
    if username in users and users[username]['password'] == password and users[username]['role'] == role:
        return jsonify({'status': True}), 200
    else:
        return jsonify({'status': False}), 200
    
@app.route('/material-upload', methods=['POST'])
def upload_material():
    # Check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    # If user does not select file, browser submits empty part
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # Accept common zip mimetypes
    valid_mimetypes = ['application/zip', 'application/x-zip-compressed', 'application/octet-stream', 'multipart/x-zip']
    if file and allowed_file(file.filename) and file.mimetype in valid_mimetypes:
        filename = secure_filename(file.filename)
        temp_dir = './material_uploads'
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir, exist_ok=True)

        try:
            # Save the zip file temporarily
            zip_path = os.path.join(temp_dir, filename)
            file.save(zip_path)
            
            # Process the zip file
            # result = process_quiz_zip(zip_path, temp_dir)

        except zipfile.BadZipFile:
            return jsonify({'error': 'Invalid zip file'}), 400
        except Exception as e:
            print(f"Error processing material zip: {str(e)}")
            return jsonify({'error': str(e)}), 500
        finally:
            if os.path.exists(zip_path):
                # Unzip the file to the material_uploads directory
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                os.remove(zip_path)
        return jsonify({'message': 'File successfully uploaded and processed'}), 200
    return jsonify({'error': 'File type not allowed or mimetype is not a recognized zip type'}), 400

@app.route('/materials', methods=['GET'])
def get_material():
    extract_dir_material = './material_uploads'
    if not os.path.exists(extract_dir_material):
        return jsonify({'error': 'No material uploaded yet'}), 404

    try:
        extracted_files = []
        for root, dirs, files in os.walk(extract_dir_material):
            for dir in dirs:
                material_data={}
                material_json_path = os.path.join(extract_dir_material, dir, 'material.json')
                if os.path.isfile(material_json_path):
                    try:
                        with open(material_json_path, 'r', encoding='utf-8') as f:
                            material_data = json.load(f)
                        extracted_files.append(material_data)
                    except Exception as e:
                        extracted_files.append({
                            'quiz_name': dir,
                            'error': f'Failed to load material.json: {str(e)}'
                        })

        return jsonify(extracted_files), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/material/<filename>', methods=['GET'])
def get_material_file(filename):
    extract_dir_material = './material_uploads'
    file_path = os.path.join(extract_dir_material, filename)
    
    if not os.path.exists(file_path):
        return jsonify({'error': f'File "{filename}" not found'}), 404
    zip_file_path = os.path.join(extract_dir_material, f"{filename}.zip")
    try:
        # Create a zip of the folder, including the folder itself as the root
        with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(file_path):
                for file in files:
                    abs_path = os.path.join(root, file)
                    # Include the chapter folder as the root in the zip
                    rel_path = os.path.relpath(abs_path, os.path.dirname(file_path))
                    zipf.write(abs_path, arcname=rel_path)
        file_size = os.path.getsize(zip_file_path)
        response = send_file(zip_file_path, as_attachment=True)
        response.headers['Content-Length'] = file_size
        return response
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# delete material
@app.route('/material-delete/<filename>', methods=['DELETE'])
def delete_material(filename):
    extract_dir_material = './material_uploads'
    file_path = os.path.join(extract_dir_material, filename)
    
    if not os.path.exists(file_path):
        return jsonify({'error': f'File "{filename}" not found'}), 404
    
    try:
        if os.path.isdir(file_path):
            shutil.rmtree(file_path)
        else:
            os.remove(file_path)
        return jsonify({'message': f'File "{filename}" deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def process_material_zip(zip_path, extract_dir_material):
    """Process the material zip file and extract its contents"""
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # Extract all files
        zip_ref.extractall(extract_dir_material)
        
        # Look for specific files in the zip
        extracted_files = zip_ref.namelist()
        
        result = {
            'files': extracted_files,
            'media_files': []
        }
        
        for file in extracted_files:
            if file.endswith(('.mp4', '.jpg', '.png', '.pdf')):
                result['media_files'].append(file)
        
        return result

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
