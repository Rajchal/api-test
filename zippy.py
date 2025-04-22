from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import zipfile
import os
import io
import json
import uuid

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = {'zip'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB limit

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/upload-quiz-zip', methods=['POST'])
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
    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/question')
def display_extracted_zip():
    folder_path ='./uploads'
    if not folder_path:
        return jsonify({'error': 'Missing folder path'}), 400

    folder_path = os.path.abspath(folder_path)
    if not os.path.exists(folder_path):
        app.logger.error(f"Provided folder path does not exist: {folder_path}")
        return jsonify({'error': 'Invalid folder path'}), 400

    extracted_files = []
    questions_data = None

    try:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = file
                extracted_files.append(file_path)
                if file == 'questions.json':
                    with open(os.path.join(root,file), 'r') as f:
                        questions_data = json.load(f)

        return jsonify({
            'extracted_files': extracted_files,
            'questions_data': questions_data
        }), 200
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
            'quiz_data': None,
            'questions': [],
            'media_files': []
        }
        
        # Example processing - you'll need to customize this
        for file in extracted_files:
            if file.endswith('quiz.json'):
                with open(os.path.join(extract_dir, file), 'r') as f:
                    result['quiz_data'] = json.load(f)
            elif file.endswith('questions.json'):
                with open(os.path.join(extract_dir, file), 'r') as f:
                    result['questions'] = json.load(f)
            elif file.startswith('media/'):
                result['media_files'].append(file)
        
        return result

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)