from client.auth import open_auth_window
from client.gui import open_chat_window

if __name__ == "__main__":
    open_auth_window(start_chat_callback=open_chat_window)
