# SQLite3 compatibility fix for Streamlit Cloud deployment
# This module must be imported BEFORE any chromadb imports

import sys

def fix_sqlite_for_chroma():
    """Fix SQLite3 version compatibility for ChromaDB on Streamlit Cloud"""
    try:
        # Try to import pysqlite3 first (prioritize it)
        import pysqlite3
        sys.modules['sqlite3'] = sys.modules['pysqlite3']
        print("✅ Using pysqlite3 for ChromaDB compatibility")
        return True
    except ImportError:
        try:
            # Fallback: check if system sqlite3 is adequate
            import sqlite3
            if hasattr(sqlite3, 'sqlite_version_info') and sqlite3.sqlite_version_info >= (3, 35, 0):
                print(f"✅ System SQLite3 {sqlite3.sqlite_version} is compatible with ChromaDB")
                return True
            else:
                print(f"❌ System SQLite3 {getattr(sqlite3, 'sqlite_version', 'unknown')} is too old for ChromaDB")
                return False
        except ImportError:
            print("❌ No SQLite3 available")
            return False

# Apply the fix immediately when this module is imported
fix_sqlite_for_chroma()