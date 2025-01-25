import os
import fitz  # PyMuPDF
from werkzeug.utils import secure_filename
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
        """
        Split text into chunks of a specified size with overlap.
        This is a simple replacement for RecursiveCharacterTextSplitter.
        """
        words = text.split()
        chunks = []
        start = 0

        while start < len(words):
            end = start + chunk_size
            chunk = " ".join(words[start:end])
            chunks.append(chunk)
            start += (chunk_size - chunk_overlap)

        return chunks

class WebService:
    @staticmethod
    def scrape_job_posting(url):
        """
        Scrape job posting from a URL.
        """
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            for element in soup(['script', 'style', 'header', 'footer', 'nav', 'meta', 'iframe']):
                element.decompose()
                
            content = soup.get_text(separator="\n", strip=True)
            
            if len(content) <= 50:
                return None  # Fallback to manual description if scraping fails
                
            return content
            
        except Exception as e:
            print(f"Error scraping job posting: {e}")
            return None
