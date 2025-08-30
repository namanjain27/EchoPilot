
from langchain_chroma import Chroma
from sentence_transformers import SentenceTransformer
import os

embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

persist_directory = 'knowledgeBase'
db_collection_name = "general_kb"

# Create directory if it doesn't exist
if not os.path.exists(persist_directory):
    os.makedirs(persist_directory)

vector_store = Chroma(
    collection_name=db_collection_name,
    embedding_function=embedding_model,
    persist_directory=persist_directory
)
