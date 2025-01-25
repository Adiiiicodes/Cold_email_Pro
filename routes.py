from flask import Blueprint, request, jsonify, render_template
from werkzeug.utils import secure_filename
import os
import uuid
from config import Config
from services import FileService, WebService
from email_Logic import EmailGenerator
from sentence_transformers import SentenceTransformer

bp = Blueprint('main', __name__)
TEMP_EMAIL_STORAGE = {}

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/generate', methods=['GET', 'POST'])
def generate_email():
    if request.method == 'GET':
        return render_template('generate.html')

    if request.method == 'POST':
        try:
            # File upload and validation logic
            if 'portfolio' not in request.files:
                return jsonify({'success': False, 'message': 'No file part in the request'})

            file = request.files['portfolio']

            # Validate uploaded file
            if not file or file.filename == '':
                return jsonify({'success': False, 'message': 'No file uploaded or file name is empty'})

            if not FileService.allowed_file(file.filename, Config.ALLOWED_EXTENSIONS):
                return jsonify({'success': False, 'message': 'Invalid file type. Only PDF files are allowed'})

            # Generate unique ID for the file
            email_id = str(uuid.uuid4())
            filename = secure_filename(file.filename)
            temp_path = os.path.join(Config.UPLOAD_FOLDER, f"{email_id}_{filename}")

            # Save and process uploaded file
            os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
            file.save(temp_path)

            portfolio_text = FileService.process_pdf(temp_path)
            if not portfolio_text.strip():
                os.remove(temp_path)
                return jsonify({'success': False, 'message': 'Uploaded PDF is empty or unreadable'})

            # Split text into chunks
            chunks = FileService.split_text(portfolio_text)

            # Job posting extraction
            job_url = request.form.get('jobUrl')
            manual_job_description = request.form.get('jobDescription')

            if not job_url and not manual_job_description:
                os.remove(temp_path)
                return jsonify({'success': False, 'message': 'Either a job URL or job description is required.'})

            job_posting_text = manual_job_description or WebService.scrape_job_posting(job_url)
            
            # Collect form data
            form_data = {key: request.form.get(key) for key in [
                'name', 'company', 'services', 'recipient', 
                'goal', 'problem', 'pastWork', 'tone', 
                'cta', 'benefits', 'signoff', 'customSignoff'
            ]}
            
            # Check for missing fields
            missing_fields = [key for key, value in form_data.items() if not value and key != 'customSignoff']
            if missing_fields:
                os.remove(temp_path)
                return jsonify({'success': False, 'message': f'Missing fields: {", ".join(missing_fields)}'})

            # Generate email
            embeddings = SentenceTransformer("all-MiniLM-L6-v2")
            email_generator = EmailGenerator(Config.GEMINI_API_KEY, embeddings)
            email_generator.store_portfolio(email_id, chunks)
            email_content = email_generator.generate_email(form_data, job_posting_text)

            # Store email data temporarily
            TEMP_EMAIL_STORAGE[email_id] = {
                'form_data': form_data,
                'email_content': email_content
            }

            # Clean up the uploaded file
            os.remove(temp_path)

            return email_content

        except Exception as e:
            print(f"Error generating email: {e}")
            return jsonify({'success': False, 'message': str(e)})
        

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/docs')
def docs():
    """Render the documentation page."""
    return render_template('docs.html')

@bp.route('/features')
def features():
    """Render the features page."""
    return render_template('features.html')

@bp.route('/guidelines')
def guidelines():
    """Render the guidelines page."""
    return render_template('guidelines.html')

@bp.route('/preview')
def preview_email():
    email_id = request.args.get('id')
    if not email_id or email_id not in TEMP_EMAIL_STORAGE:
        return "Email not found", 404
    
    email_data = TEMP_EMAIL_STORAGE[email_id]
    email_content = email_data.get('email_content', 'Email content is not available.')
    return render_template('preview.html', email_content=email_content, email_id=email_id)

@bp.route('/modify_email', methods=['POST'])
def modify_email():
    email_id = request.json.get('emailId')
    modified_content = request.json.get('content')
    
    if not email_id or email_id not in TEMP_EMAIL_STORAGE:
        return jsonify({'success': False, 'message': 'Email not found'})
    
    TEMP_EMAIL_STORAGE[email_id]['email_content'] = modified_content
    return jsonify({'success': True})
