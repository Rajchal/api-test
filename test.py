from flask import Flask, jsonify
from flask_socketio import SocketIO, emit
import socket
from flask_cors import CORS 
# Initialize Flask and Flask-SocketIO
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
CORS(app)  # Enable CORS for the entire app
socketio = SocketIO(app, cors_allowed_origins="*")

# The shared JSON object
shared_data = {
    "message": "Hello, llWorld!",
    "counter": 0
}

# Endpoint to fetch the current object
@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify(shared_data)

# Function to modify the shared data (example: increment counter)
@socketio.on('update')
def update_data(new_data):
    global shared_data
    shared_data.update(new_data)  # Update the shared data
    emit('update', shared_data, broadcast=True)  # Broadcast the updated data to all clients

if __name__ == '__main__':
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(f"Server is running on IP: {local_ip}")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)