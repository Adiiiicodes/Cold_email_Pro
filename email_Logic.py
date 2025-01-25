from typing import Dict, Any
import google.generativeai as genai
import chromadb
from sentence_transformers import SentenceTransformer
from config import Config

class EmailGenerator:
    def __init__(self, api_key, embeddings):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        self.embeddings = embeddings
        self.chroma_client = chromadb.PersistentClient(path=Config.CHROMA_PERSIST_DIRECTORY)

    def create_email_prompt(self, form_data: Dict[str, Any], job_posting_text: str) -> str:
        return f"""
        Generate a professional email using the following information:
        Sender's Name: {form_data['name']}
        Company: {form_data['company']}
        Services Offered: {form_data['services']}
        Recipient: {form_data['recipient']}
        Goal: {form_data['goal']}
        Problem to Solve: {form_data['problem']}
        Past Work Experience: {form_data['pastWork']}
        Desired Tone: {form_data['tone']}
        Call to Action: {form_data['cta']}
        Benefits: {form_data['benefits']}
        
        Job Posting Details:
        {job_posting_text}

        Create a persuasive email that:
        1. Maintains a {form_data['tone']} tone
        2. Clearly addresses the recipient's needs from the job posting
        3. Highlights relevant experience and benefits
        4. Includes a clear call to action
        5. Uses the provided sign-off: {form_data['customSignoff'] if form_data['customSignoff'] else form_data['signoff']}
        """

    def generate_email(self, form_data: Dict[str, Any], job_posting_text: str) -> str:
        prompt = self.create_email_prompt(form_data, job_posting_text)
        response = self.model.generate_content(prompt)
        return response.text

    def store_portfolio(self, email_id: str, chunks: list):
        collection = self.chroma_client.create_collection(
            name=f"portfolio_{email_id}",
            embedding_function=self.embeddings.encode
        )
        
        for i, chunk in enumerate(chunks):
            embedding = self.embeddings.encode([chunk])[0]
            collection.add(
                embeddings=[embedding],
                documents=[chunk],
                ids=[f"chunk_{i}"]
            )
        return collection