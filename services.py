import os
import fitz  # PyMuPDF
from werkzeug.utils import secure_filename
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from bs4 import BeautifulSoup
import requests

class FileService:
    @staticmethod
    def allowed_file(filename, allowed_extensions):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

    @staticmethod
    def process_pdf(file_path):
        """Extract text from PDF using PyMuPDF."""
        text = ""
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text()
        return text

    @staticmethod
    def split_text(text, chunk_size=1000, chunk_overlap=200):
        """Split text into chunks using RecursiveCharacterTextSplitter."""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        return splitter.split_text(text)

class WebService:
    @staticmethod
    def scrape_job_posting(url, fallback_description):
        """
        Scrape job posting from a URL.
        Falls back to user-provided description if scraping fails.
        """
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            for element in soup(['script', 'style', 'header', 'footer', 'nav', 'meta', 'iframe']):
                element.decompose()
                
            content = soup.get_text(separator="\n", strip=True)
            
            if len(content) <= 50:
                return fallback_description
                
            return content
            
        except Exception as e:
            print(f"Error scraping job posting: {e}")
            return fallback_description