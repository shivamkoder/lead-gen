"""
Application Entry Point
Run the Flask application
"""

"""Legacy run script updated to new structure."""

import os
from backend.app import app

if __name__ == '__main__':
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    app.run(host=host, port=port, debug=debug)

