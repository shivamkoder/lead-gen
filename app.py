import os
from dotenv import load_dotenv
from flask import Flask
from backend.database.db import db, migrate
from backend.config import config

# Load environment variables from .env file
load_dotenv()

# import blueprints from routes
# individual blueprints will be auto-discovered by register_routes


def create_app(config_name=None):
    """Application factory for the leadgen platform backend."""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # register blueprints automatically
    from backend.routes import register_routes
    register_routes(app)

    return app


# Create app instance for production (Render/gunicorn)
app = create_app()
@app.route("/")
def home():
     return "Render deployment working"


if __name__ == "__main__":
    # Development server
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    app.run(host=host, port=port)
