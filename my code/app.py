import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask

def create_app():
    app = Flask(__name__)

    @app.route('/')
    def home():
        return "<h1>PPC Platform is live</h1>", 200

    @app.route('/health')
    def health():
        return {"status": "ok"}, 200

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

