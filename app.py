from flask import Flask, request, jsonify, render_template, session
from werkzeug.utils import secure_filename
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from langchain_text_splitters import CharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import requests
from bs4 import BeautifulSoup
import PyPDF2
import uuid
import json

app = Flask(__name__)
app.secret_key = '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'  # Change this to a secure secret key

# Configuration
UPLOAD_FOLDER = 'temp_uploads'
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB max file size
ALLOWED_EXTENSIONS = {'pdf'}
TEMP_EMAIL_STORAGE = {}

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize embeddings
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")

# Initialize ChromaDB
chroma_persist_directory = "chroma_db"
os.makedirs(chroma_persist_directory, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_pdf(file_path):
    """Extract text from PDF."""
    text = ""
    with open(file_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def split_text(text, chunk_size=1000, chunk_overlap=200):
    """Split text into chunks using the text splitter."""
    splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    return splitter.split_text(text)

def scrape_job_posting(url):
    """Scrape job posting from URL."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
            
        # Get text and clean it
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    except Exception as e:
        print(f"Error scraping job posting: {str(e)}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['GET', 'POST'])
def generate_email():
    if request.method == 'GET':
        # Simply render the form (generate.html)
        return render_template('generate.html')
    
    if request.method == 'POST':
        try:
            # Check if 'portfolio' is part of the request
            if 'portfolio' not in request.files:
                return jsonify({'success': False, 'message': 'No file uploaded'})

            file = request.files['portfolio']
            if file.filename == '':
                return jsonify({'success': False, 'message': 'No file selected'})

            if not allowed_file(file.filename):
                return jsonify({'success': False, 'message': 'Invalid file type'})

            # Handle file upload if it's valid
            email_id = str(uuid.uuid4())
            filename = secure_filename(file.filename)
            temp_path = os.path.join(UPLOAD_FOLDER, f"{email_id}_{filename}")
            file.save(temp_path)
            
            # Process the uploaded file (assuming process_pdf and split_text functions)
            portfolio_text = process_pdf(temp_path)
            chunks = split_text(portfolio_text)
        
            # Create embeddings and store in ChromaDB
            vectorstore = Chroma(
                collection_name=f"portfolio_{email_id}",
                embedding_function=embeddings,
                persist_directory=chroma_persist_directory
            )
        
            # Add documents to vector store
            vectorstore.add_texts(chunks)
        
            # Scrape job posting
            job_url = request.form.get('jobUrl')
            job_posting_text = scrape_job_posting(job_url)
        
            if not job_posting_text:
                return jsonify({'success': False, 'message': 'Failed to scrape job posting'})
        
            # Collect form data
            form_data = {
                'name': request.form.get('name'),
                'company': request.form.get('company'),
                'services': request.form.get('services'),
                'recipient': request.form.get('recipient'),
                'goal': request.form.get('goal'),
                'problem': request.form.get('problem'),
                'pastWork': request.form.get('pastWork'),
                'tone': request.form.get('tone'),
                'cta': request.form.get('cta'),
                'benefits': request.form.get('benefits'),
                'deadline': request.form.get('deadline'),
                'signoff': request.form.get('signoff'),
                'customSignoff': request.form.get('customSignoff'),
                'portfolio_chunks': chunks,
                'job_posting': job_posting_text
            }
        
            # Store form data temporarily
            TEMP_EMAIL_STORAGE[email_id] = form_data
        
            # Clean up temporary file
            os.remove(temp_path)
        
            return jsonify({
                'success': True,
                'emailId': email_id
            })
        
        except Exception as e:
            print(f"Error: {str(e)}")
            return jsonify({'success': False, 'message': str(e)})

        

@app.route('/preview')
def preview_email():
    email_id = request.args.get('id')
    if not email_id or email_id not in TEMP_EMAIL_STORAGE:
        return "Email not found", 404
    
    email_data = TEMP_EMAIL_STORAGE[email_id]
    return render_template('preview.html', email_data=email_data)

@app.route('/modify_email', methods=['POST'])
def modify_email():
    email_id = request.json.get('emailId')
    modified_content = request.json.get('content')
    
    if not email_id or email_id not in TEMP_EMAIL_STORAGE:
        return jsonify({'success': False, 'message': 'Email not found'})
    
    TEMP_EMAIL_STORAGE[email_id]['modified_content'] = modified_content
    return jsonify({'success': True})

@app.route('/finalize_email', methods=['POST'])
def finalize_email():
    email_id = request.json.get('emailId')
    
    if not email_id or email_id not in TEMP_EMAIL_STORAGE:
        return jsonify({'success': False, 'message': 'Email not found'})
    
    # Clean up ChromaDB collection
    try:
        vectorstore = Chroma(
            collection_name=f"portfolio_{email_id}",
            embedding_function=embeddings,
            persist_directory=chroma_persist_directory
        )
        vectorstore.delete_collection()
    except Exception as e:
        print(f"Error cleaning up ChromaDB: {str(e)}")
    
    # Remove from temporary storage
    email_data = TEMP_EMAIL_STORAGE.pop(email_id)
    
    return jsonify({
        'success': True,
        'final_content': email_data.get('modified_content', '')
    })

@app.route('/docs')
def docs():
    return render_template('docs.html')

@app.route('/features')
def features():
    return render_template('features.html')

@app.route('/guidelines')
def guidelines():
    return render_template('guidelines.html')

if __name__ == '__main__':
    app.run(debug=True)
