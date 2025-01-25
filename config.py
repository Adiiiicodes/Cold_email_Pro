import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    UPLOAD_FOLDER = 'temp_uploads'
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB max file size
    ALLOWED_EXTENSIONS = {'pdf'}
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    CHROMA_PERSIST_DIRECTORY = "chroma_db"
    
    @staticmethod
    def init_app(app):
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.CHROMA_PERSIST_DIRECTORY, exist_ok=True)