"""
Main entry point for EchoPilot application
Run with: streamlit run app.py
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import and run the main Streamlit app
from src.ui.streamlit_app import main

if __name__ == "__main__":
    main()