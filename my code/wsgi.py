"""WSGI entry point for production deployment."""
import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

from backend.app import create_app
from backend.app.config import ProductionConfig

# Create app instance with production config
app = create_app(ProductionConfig)

if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    app.run(host=host, port=port)
