import sys
import os

from .loader import load_messages
from .model_builder import build_rows
from .ui import ChatViewer

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py chats.json")
        return

    path = sys.argv[1]
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return

    try:
        messages = load_messages(path)
        rows = build_rows(messages)
    except Exception as e:
        print(f"Error: {e}")
        return

    app = ChatViewer(rows)
    app.mainloop()

if __name__ == "__main__":
    main()
