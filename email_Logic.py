from typing import Dict, Any, List
import google.generativeai as genai
import chromadb
from sentence_transformers import SentenceTransformer
from config import Config

class SentenceTransformerEmbeddingFunction:
    """
    A wrapper class for SentenceTransformer to comply with ChromaDB's EmbeddingFunction interface.
    """
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.embeddings = SentenceTransformer(model_name)

    def __call__(self, input: List[str]) -> List[List[float]]:
        """
        Encodes a list of texts into embeddings.
        
        Args:
            input (List[str]): A list of text strings to encode.
        
        Returns:
            List[List[float]]: A list of embeddings, where each embedding is a list of floats.
        """
        return self.embeddings.encode(input).tolist()

class EmailGenerator:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        self.embeddings = SentenceTransformerEmbeddingFunction()  # Use the wrapper class
        self.chroma_client = chromadb.PersistentClient(path=Config.CHROMA_PERSIST_DIRECTORY)

    def create_email_prompt(self, form_data: Dict[str, Any], job_posting_text: str) -> str:
        """
        Creates a prompt for generating an email based on form data and job posting text.
        
        Args:
            form_data (Dict[str, Any]): A dictionary containing form data.
            job_posting_text (str): The text of the job posting.
        
        Returns:
            str: A formatted prompt for the email generation model.
        """
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
        """
        Generates an email using the Gemini model.
        
        Args:
            form_data (Dict[str, Any]): A dictionary containing form data.
            job_posting_text (str): The text of the job posting.
        
        Returns:
            str: The generated email content.
        """
        prompt = self.create_email_prompt(form_data, job_posting_text)
        response = self.model.generate_content(prompt)
        return response.text

    def store_portfolio(self, email_id: str, chunks: List[str]):
        """
        Stores portfolio chunks in ChromaDB with embeddings.
        
        Args:
            email_id (str): A unique identifier for the email/portfolio.
            chunks (List[str]): A list of text chunks to store.
        
        Returns:
            chromadb.Collection: The ChromaDB collection where the chunks are stored.
        """
        # Create a collection with the custom embedding function
        collection = self.chroma_client.create_collection(
            name=f"portfolio_{email_id}",
            embedding_function=SentenceTransformerEmbeddingFunction()  # Use the wrapper class
        )
        
        # Add documents to the collection
        for i, chunk in enumerate(chunks):
            collection.add(
                documents=[chunk],  # Pass the chunk as a document
                ids=[f"chunk_{i}"]  # Assign a unique ID to each chunk
            )
        return collection
