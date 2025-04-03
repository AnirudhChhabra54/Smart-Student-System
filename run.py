import os
import subprocess
import signal
import sys
from flask import Flask, send_from_directory
from backend.app import create_app

# Create Flask application instances
frontend_app = Flask(__name__, static_folder='frontend')
backend_app = create_app()

# Serve frontend files
@frontend_app.route('/')
def serve_index():
    return send_from_directory('frontend', 'index.html')

@frontend_app.route('/dashboard')
def serve_dashboard():
    return send_from_directory('frontend', 'dashboard.html')

@frontend_app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('frontend', path)

def run_backend():
    """Run the backend server"""
    backend_app.run(host='0.0.0.0', port=5000)

def run_frontend():
    """Run the frontend server"""
    frontend_app.run(host='0.0.0.0', port=8000)

if __name__ == '__main__':
    try:
        # Start the backend server
        backend_process = subprocess.Popen([
            sys.executable, '-c',
            'from run import run_backend; run_backend()'
        ])
        
        # Start the frontend server
        frontend_process = subprocess.Popen([
            sys.executable, '-c',
            'from run import run_frontend; run_frontend()'
        ])
        
        print("Servers started successfully!")
        print("Frontend server running at http://localhost:8000")
        print("Backend server running at http://localhost:5000")
        print("Press Ctrl+C to stop the servers")
        
        # Wait for processes to complete
        backend_process.wait()
        frontend_process.wait()
        
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        # Send termination signal to both processes
        backend_process.send_signal(signal.SIGTERM)
        frontend_process.send_signal(signal.SIGTERM)
        # Wait for processes to terminate
        backend_process.wait()
        frontend_process.wait()
        print("Servers stopped successfully!")
        sys.exit(0)