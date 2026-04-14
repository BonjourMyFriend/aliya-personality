"""
Aliya Chat — Bring the game character to life.

Usage:
  1. Put your API key in ../.env  (API_KEY=sk-...)
  2. pip install customtkinter pillow openai python-dotenv
  3. python main.py
"""
import sys
from pathlib import Path

# Load .env before importing config
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from config import DB_PATH, API_KEY
from memory import Memory
from chat_engine import ChatEngine
from ui import AliyaWindow


def main():
    if not API_KEY or API_KEY == "your_api_key_here":
        print("ERROR: Set your API_KEY in the .env file!")
        print(f"  Edit: {Path(__file__).parent.parent / '.env'}")
        sys.exit(1)

    # Initialize storage
    memory = Memory(DB_PATH)

    # Get or create session
    session_id = memory.get_active_session()
    if session_id is None:
        session_id = memory.create_session("Chat")

    # Initialize chat engine
    engine = ChatEngine(memory)

    # Launch UI
    window = AliyaWindow(engine, memory, session_id)
    window.mainloop()


if __name__ == "__main__":
    main()
