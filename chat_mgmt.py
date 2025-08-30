import os
import json
from langchain_core.messages import HumanMessage, AIMessage

# Chat history file path
CHAT_HISTORY_FILE = "chat_history.txt"

def load_chat_history():
    """Load chat history from file if it exists."""
    chat_history = []
    if os.path.exists(CHAT_HISTORY_FILE):
        try:
            with open(CHAT_HISTORY_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        data = json.loads(line)
                        if data['type'] == 'human':
                            chat_history.append(HumanMessage(content=data['content']))
                        elif data['type'] == 'ai':
                            chat_history.append(AIMessage(content=data['content']))
        except Exception as e:
            print(f"Error loading chat history: {e}")
            chat_history = []
    return chat_history

def save_chat_history(chat_history):
    """Save chat history to file."""
    try:
        with open(CHAT_HISTORY_FILE, 'w', encoding='utf-8') as f:
            for message in chat_history:
                if isinstance(message, HumanMessage):
                    f.write(json.dumps({"type": "human", "content": message.content}) + '\n')
                elif isinstance(message, AIMessage):
                    f.write(json.dumps({"type": "ai", "content": message.content}) + '\n')
        print(f"Chat history saved to {CHAT_HISTORY_FILE}")
    except Exception as e:
        print(f"Error saving chat history: {e}")
