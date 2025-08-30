import os
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
import logging
import docx2txt
from pathlib import Path
from langchain.schema import Document
from services import vector_store

## want this to be a separate layer for data ingestion into the vector db - chromaDB
## a function that takes multi-file input and stores them in the vector db
logger = logging.getLogger(__name__)

## ------Extraction processors--------
def extract_docx(file_path) -> list:
    """Extract text from DOCX files and return as Document list"""
    text = docx2txt.process(file_path) 
    document = Document(page_content=text, metadata={"source": str(file_path)})
    return [document]

def extract_pdf(file_path) -> list:
    """Extract text from PDF files and return as Document list"""
    pdf_loader = PyPDFLoader(file_path) 
    try:
        pages = pdf_loader.load()
        print(f"PDF has been loaded and has {len(pages)} pages")
        return pages
    except Exception as e:
        print(f"Error loading PDF: {e}")
        return None

def extract_txt(file_path) -> list:
    """Extract text from TXT and MD files and return as Document list"""
    loader = TextLoader(file_path, encoding="utf-8")
    return loader.load()  # returns List[Document]

## ----------main ingestion---------
def ingest_file_to_vectordb(file_path: str) -> None:
    """
    Main function to ingest a file into ChromaDB vector store
    Supports: PDF, DOCX, TXT, MD file extensions
    
    Args:
        file_path (str): Path to the file to ingest
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file extension is not supported
        Exception: For other processing errors
    """
    # Supported file processors mapping
    supported_types = {
        '.pdf': extract_pdf,
        '.docx': extract_docx,
        '.txt': extract_txt,
        '.md': extract_txt
    }
    
    file_path = Path(file_path)
    
    # Check if file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    file_extension = file_path.suffix.lower()
    
    # Check if file extension is supported
    if file_extension not in supported_types:
        raise ValueError(f"Unsupported file extension: {file_extension}. Supported types: {list(supported_types.keys())}")
    
    # Process file based on type
    processor = supported_types[file_extension]
    file_content = processor(str(file_path))
    
    if not file_content:
        logger.warning(f"No content extracted from: {file_path}")
        return
    
    # Chunking Process initiate
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    
    pages_split = text_splitter.split_documents(file_content)
    
    # Store in vector DB
    try:
        vector_store.add_documents(documents = pages_split)
        print(f"Successfully ingested {file_path.name} into ChromaDB vector store!")
        
    except Exception as e:
        print(f"Error setting up ChromaDB: {str(e)}")
        raise
        
if __name__ == "__main__":
    file_path = input("Give the file path to ingest: ")
    try:
        ingest_file_to_vectordb(file_path)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
