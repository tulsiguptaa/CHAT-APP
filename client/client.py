import socket
import json
import threading
from config import settings

class ChatClient:
    def __init__(self, username, room='general'):
        self.username = username
        self.room = room
        self.socket = None
        self.connected = False
        self.message_callback = None
        self.status_callback = None
        
    def connect(self):
        """Connect to the server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((settings.HOST, settings.PORT))
            self.connected = True
            
            # Join the room
            join_msg = {
                'type': 'join',
                'username': self.username,
                'room': self.room
            }
            self.send_message(join_msg)
            
            # Start listening thread
            listen_thread = threading.Thread(target=self._listen_for_messages)
            listen_thread.daemon = True
            listen_thread.start()
            
            return True
            
        except Exception as e:
            if settings.DEBUG:
                print(f"Connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from server"""
        self.connected = False
        if self.socket:
            self.socket.close()
    
    def send_message(self, message):
        """Send a message to the server"""
        if self.connected and self.socket:
            try:
                # For large file messages, split into smaller chunks
                if message.get('type') == 'file':
                    return self.send_large_message(message)
                else:
                    self.socket.send(json.dumps(message).encode(settings.ENCODING))
                    return True
            except Exception as e:
                if settings.DEBUG:
                    print(f"Send error: {e}")
                self.connected = False
                return False
        return False
    
    def send_large_message(self, message):
        """Send large messages in chunks to avoid buffer overflow"""
        try:
            # Convert message to JSON string
            message_str = json.dumps(message)
            message_bytes = message_str.encode(settings.ENCODING)
            
            # If message is small enough, send normally
            if len(message_bytes) <= settings.BUFFER_SIZE:
                self.socket.send(message_bytes)
                return True
            
            # For large messages, send in chunks
            chunk_size = settings.BUFFER_SIZE // 2  # Use half buffer size for safety
            total_chunks = (len(message_bytes) + chunk_size - 1) // chunk_size
            
            # Send message header
            header = {
                'type': 'large_message_start',
                'total_size': len(message_bytes),
                'total_chunks': total_chunks
            }
            self.socket.send(json.dumps(header).encode(settings.ENCODING))
            
            # Send chunks
            for i in range(0, len(message_bytes), chunk_size):
                chunk = message_bytes[i:i + chunk_size]
                chunk_msg = {
                    'type': 'large_message_chunk',
                    'chunk_index': i // chunk_size,
                    'chunk_data': chunk.hex()  # Convert to hex for JSON compatibility
                }
                self.socket.send(json.dumps(chunk_msg).encode(settings.ENCODING))
            
            # Send end marker
            end_msg = {'type': 'large_message_end'}
            self.socket.send(json.dumps(end_msg).encode(settings.ENCODING))
            
            return True
            
        except Exception as e:
            if settings.DEBUG:
                print(f"Large message send error: {e}")
            return False
    
    def send_chat_message(self, content):
        """Send a chat message"""
        message = {
            'type': 'message',
            'content': content
        }
        return self.send_message(message)
    
    def send_file_message(self, file_message):
        """Send a file message"""
        return self.send_message(file_message)
    
    def change_room(self, new_room):
        """Change to a different chat room"""
        message = {
            'type': 'change_room',
            'room': new_room
        }
        if self.send_message(message):
            self.room = new_room
            return True
        return False
    
    def _listen_for_messages(self):
        """Listen for incoming messages from server"""
        while self.connected:
            try:
                data = self.socket.recv(settings.BUFFER_SIZE).decode(settings.ENCODING)
                if not data:
                    break
                
                message = json.loads(data)
                
                if self.message_callback:
                    self.message_callback(message)
                    
            except Exception as e:
                if settings.DEBUG:
                    print(f"Receive error: {e}")
                break
        
        self.connected = False
        if self.status_callback:
            self.status_callback("Disconnected")
    
    def set_message_callback(self, callback):
        """Set callback for incoming messages"""
        self.message_callback = callback
    
    def set_status_callback(self, callback):
        """Set callback for connection status changes"""
        self.status_callback = callback
