"""WSGI entry point for production deployment."""
import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app

# Create app instance
app = create_app(os.getenv('FLASK_ENV', 'production'))

if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    app.run(host=host, port=port)
