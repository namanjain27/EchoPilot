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
def ingest_file_to_vectordb(file_paths) -> None:
    """
    Main function to ingest one or multiple files into ChromaDB vector store
    Supports: PDF, DOCX, TXT, MD file extensions
    
    Args:
        file_paths (str or list): Path(s) to the file(s) to ingest
        
    Note:
        Skips unsupported or missing files and continues processing others
    """
    # Supported file processors mapping
    supported_types = {
        '.pdf': extract_pdf,
        '.docx': extract_docx,
        '.txt': extract_txt,
        '.md': extract_txt
    }
    
    # Convert single file path to list for uniform processing
    if isinstance(file_paths, str):
        file_paths = [file_paths]
    
    successful_files = []
    
    for file_path in file_paths:
        try:
            file_path = Path(file_path)
            
            # Check if file exists
            if not os.path.exists(file_path):
                print(f"Skipping: File not found - {file_path}")
                continue
            
            file_extension = file_path.suffix.lower()
            
            # Check if file extension is supported
            if file_extension not in supported_types:
                print(f"Skipping: Unsupported file type - {file_path}")
                continue
            
            # Process file based on type
            processor = supported_types[file_extension]
            file_content = processor(str(file_path))
            
            if not file_content:
                logger.warning(f"No content extracted from: {file_path}")
                continue
            
            # Chunking Process initiate
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            
            pages_split = text_splitter.split_documents(file_content)
            
            # Store in vector DB
            vector_store.add_documents(documents = pages_split)
            print(f"Successfully ingested {file_path.name}")
            successful_files.append(file_path.name)
            
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
            continue
    
    if successful_files:
        print(f"Total files processed: {len(successful_files)}")
    else:
        print("No files were successfully processed")
        
if __name__ == "__main__":
    file_paths_input = input("Give the file path(s) to ingest (comma-separated for multiple): ")
    file_paths = [path.strip() for path in file_paths_input.split(',')]
    ingest_file_to_vectordb(file_paths)
