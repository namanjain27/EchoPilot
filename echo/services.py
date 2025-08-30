
from langchain_chroma import Chroma
from sentence_transformers import SentenceTransformer
import os

class SentenceTransformerEmbeddings:
    def __init__(self, model_name: str):
        self.model = SentenceTransformer(model_name)
    
    def embed_documents(self, texts):
        return self.model.encode(texts).tolist()
    
    def embed_query(self, text):
        return self.model.encode([text])[0].tolist()

embedding_model = SentenceTransformerEmbeddings('sentence-transformers/all-MiniLM-L6-v2')

persist_directory = 'knowledgeBase'
db_collection_name = "general_rentomojo"

# Create directory if it doesn't exist
if not os.path.exists(persist_directory):
    os.makedirs(persist_directory)

vector_store = Chroma(
    collection_name=db_collection_name,
    embedding_function=embedding_model,
    persist_directory=persist_directory
)
