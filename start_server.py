#!/usr/bin/env python3
"""
Server launcher script for the chat application.
Run this to start the chat server.
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from server.server import ChatServer
    print("🚀 Starting Chat Server...")
    print("=" * 50)
    
    server = ChatServer()
    server.start()
    
except KeyboardInterrupt:
    print("\n🛑 Server stopped by user")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure all dependencies are installed: pip install -r requirements.txt")
except Exception as e:
    print(f"❌ Server error: {e}")
    print("Check if the port is already in use or firewall settings") 