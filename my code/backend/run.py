"""
Application Entry Point
Run the Flask application
"""

import os
from app import create_app
from app.config import config
from app.extensions import socketio

# Get environment from environment variable
env = os.environ.get('FLASK_ENV', 'development')

# Create application instance
app = create_app(config.get(env, config['default']))


if __name__ == '__main__':
    # Run the application via SocketIO for realtime support
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    socketio.run(
        app,
        host=host,
        port=port,
        debug=debug
    )
