import os
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
import logging
import docx2txt
from pathlib import Path
from langchain.schema import Document

## want this to be a separate layer for data ingestion into the vector db - chromaDB
## a function that takes multi-file input and stores them in the vector db
logger = logging.getLogger(__name__)

def extract_docx(file_path) -> str:
    text = docx2txt.process(file_path) 
    document = Document(page_content=text, metadata={"source": str(file_path)})
    return [document]

def extract_pdf(file_path):
    pdf_loader = PyPDFLoader(file_path) 
    try:
        pages = pdf_loader.load()
        print(f"PDF has been loaded and has {len(pages)} pages")
        return pages
    except Exception as e:
        print(f"Error loading PDF: {e}")
        return None

# This works for both .txt and .md files.
def extract_txt(file_path):
    loader = TextLoader(file_path, encoding="utf-8")
    return loader.load()  # returns List[Document]

# allowed file ext. - pdf, docx, txt, md 
file_path = r'knowledgeBaseFiles\Amazon_faq_sada.docx'
file_path = Path(file_path)
file_extension = file_path.suffix.lower()

if not os.path.exists(file_path):
    raise FileNotFoundError(f"PDF file not found: {file_path}")

# Process file based on type
# text extraction begins

# processor = self.supported_types[file_extension]
# file_content = processor(str(file_path))
file_content = extract_docx(file_path) # List[Docs]

if not file_content:
    logger.warning(f"No content extracted from: {file_path}") #return empty

# Chunking Process initiate
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)

pages_split = text_splitter.split_documents(file_content) # We now apply this to our pages

persist_directory = r"D:\codes\EchoPilot\knowledgeBaseFiles"
collection_name = "kb_general"
# If our collection does not exist in the directory, we create using the os command
if not os.path.exists(persist_directory):
    os.makedirs(persist_directory)


# encoding - create embeddings
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")

# store them in the vector DB
try:
    vectorstore = Chroma.from_documents(
        documents=pages_split,
        embedding=embeddings,
        persist_directory=persist_directory,
        collection_name=collection_name
    )
    print(f"Created ChromaDB vector store!")
    
except Exception as e:
    print(f"Error setting up ChromaDB: {str(e)}")
    raise
