# app.py (main application file)
from flask import Flask
from config import Config
from routes import bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    Config.init_app(app)
    
    # Register blueprints
    app.register_blueprint(bp)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
