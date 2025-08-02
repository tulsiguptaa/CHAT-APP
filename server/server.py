import socket
import threading
import json
import time
from datetime import datetime
from config import settings
import os

class ChatServer:
    def __init__(self):
        self.host = settings.HOST
        self.port = settings.PORT
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Store active connections and rooms
        self.clients = {}  # {client_socket: {'username': str, 'room': str}}
        self.rooms = {
            'general': [],
            'random': [],
            'tech': [],
            'gaming': []
        }
        self.chat_history = self.load_chat_history()
        
        # Large message transfer state
        self.large_messages = {}  # {client_socket: {'data': b'', 'total_size': 0, 'received_size': 0}}
        
    def load_chat_history(self):
        if os.path.exists(settings.CHAT_LOG_PATH):
            try:
                with open(settings.CHAT_LOG_PATH, 'r') as f:
                    return json.load(f)
            except:
                return {'general': [], 'random': [], 'tech': [], 'gaming': []}
        return {'general': [], 'random': [], 'tech': [], 'gaming': []}
    
    def save_chat_history(self):
        with open(settings.CHAT_LOG_PATH, 'w') as f:
            json.dump(self.chat_history, f, indent=2)
    
    def broadcast(self, message, room, sender_socket=None):
        """Send message to all clients in a room"""
        for client_socket in self.rooms[room]:
            if client_socket != sender_socket:
                try:
                    client_socket.send(message.encode(settings.ENCODING))
                except:
                    self.remove_client(client_socket)
    
    def remove_client(self, client_socket):
        """Remove client from server"""
        if client_socket in self.clients:
            username = self.clients[client_socket]['username']
            room = self.clients[client_socket]['room']
            
            if room in self.rooms and client_socket in self.rooms[room]:
                self.rooms[room].remove(client_socket)
            
            del self.clients[client_socket]
            client_socket.close()
            
            # Notify others in the room
            leave_msg = json.dumps({
                'type': 'user_left',
                'username': username,
                'room': room,
                'timestamp': datetime.now().strftime('%H:%M:%S')
            })
            self.broadcast(leave_msg, room)
    
    def handle_client(self, client_socket, address):
        """Handle individual client connection"""
        try:
            while True:
                message = client_socket.recv(settings.BUFFER_SIZE).decode(settings.ENCODING)
                if not message:
                    break
                
                data = json.loads(message)
                msg_type = data.get('type')
                
                # Handle large message transfer
                if msg_type == 'large_message_start':
                    self.handle_large_message_start(client_socket, data)
                elif msg_type == 'large_message_chunk':
                    self.handle_large_message_chunk(client_socket, data)
                elif msg_type == 'large_message_end':
                    self.handle_large_message_end(client_socket)
                
                if msg_type == 'join':
                    username = data['username']
                    room = data['room']
                    
                    self.clients[client_socket] = {'username': username, 'room': room}
                    self.rooms[room].append(client_socket)
                    
                    # Send room history
                    history_msg = json.dumps({
                        'type': 'history',
                        'messages': self.chat_history[room][-50:]  # Last 50 messages
                    })
                    client_socket.send(history_msg.encode(settings.ENCODING))
                    
                    # Notify others
                    join_msg = json.dumps({
                        'type': 'user_joined',
                        'username': username,
                        'room': room,
                        'timestamp': datetime.now().strftime('%H:%M:%S')
                    })
                    self.broadcast(join_msg, room)
                
                elif msg_type == 'message':
                    username = self.clients[client_socket]['username']
                    room = self.clients[client_socket]['room']
                    content = data['content']
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    
                    # Store message
                    message_data = {
                        'username': username,
                        'content': content,
                        'timestamp': timestamp
                    }
                    self.chat_history[room].append(message_data)
                    
                    # Broadcast to room
                    broadcast_msg = json.dumps({
                        'type': 'message',
                        'username': username,
                        'content': content,
                        'timestamp': timestamp,
                        'room': room
                    })
                    self.broadcast(broadcast_msg, room, client_socket)
                    
                    # Save periodically
                    if len(self.chat_history[room]) % 10 == 0:
                        self.save_chat_history()
                

                
                elif msg_type == 'change_room':
                    old_room = self.clients[client_socket]['room']
                    new_room = data['room']
                    username = self.clients[client_socket]['username']
                    
                    # Remove from old room
                    if client_socket in self.rooms[old_room]:
                        self.rooms[old_room].remove(client_socket)
                    
                    # Add to new room
                    self.rooms[new_room].append(client_socket)
                    self.clients[client_socket]['room'] = new_room
                    
                    # Send new room history
                    history_msg = json.dumps({
                        'type': 'history',
                        'messages': self.chat_history[new_room][-50:]
                    })
                    client_socket.send(history_msg.encode(settings.ENCODING))
                    
                    # Notify both rooms
                    leave_msg = json.dumps({
                        'type': 'user_left',
                        'username': username,
                        'room': old_room,
                        'timestamp': datetime.now().strftime('%H:%M:%S')
                    })
                    self.broadcast(leave_msg, old_room)
                    
                    join_msg = json.dumps({
                        'type': 'user_joined',
                        'username': username,
                        'room': new_room,
                        'timestamp': datetime.now().strftime('%H:%M:%S')
                    })
                    self.broadcast(join_msg, new_room)
        
        except Exception as e:
            if settings.DEBUG:
                print(f"Client error: {e}")
        finally:
            # Clean up large message state
            if client_socket in self.large_messages:
                del self.large_messages[client_socket]
            self.remove_client(client_socket)
    
    def handle_large_message_start(self, client_socket, data):
        """Handle large message transfer start"""
        try:
            # Initialize large message state
            self.large_messages[client_socket] = {
                'data': b'',
                'total_size': data['total_size'],
                'received_size': 0
            }
            
        except Exception as e:
            if settings.DEBUG:
                print(f"Large message start error: {e}")
    
    def handle_large_message_chunk(self, client_socket, data):
        """Handle large message chunk"""
        try:
            if client_socket in self.large_messages:
                # Convert hex back to bytes and append
                chunk_data = bytes.fromhex(data['chunk_data'])
                self.large_messages[client_socket]['data'] += chunk_data
                self.large_messages[client_socket]['received_size'] += len(chunk_data)
            
        except Exception as e:
            if settings.DEBUG:
                print(f"Large message chunk error: {e}")
    
    def handle_large_message_end(self, client_socket):
        """Handle large message transfer end and process"""
        try:
            if client_socket in self.large_messages:
                # Reconstruct the original message
                message_data = self.large_messages[client_socket]['data']
                message_str = message_data.decode(settings.ENCODING)
                original_message = json.loads(message_str)
                
                # Process the message based on its type
                msg_type = original_message.get('type')
                
                if msg_type == 'file':
                    self.process_file_message(client_socket, original_message)
                elif msg_type == 'message':
                    self.process_chat_message(client_socket, original_message)
                
                # Clean up large message state
                del self.large_messages[client_socket]
            
        except Exception as e:
            if settings.DEBUG:
                print(f"Large message end error: {e}")
    
    def process_file_message(self, client_socket, message):
        """Process a file message"""
        try:
            username = self.clients[client_socket]['username']
            room = self.clients[client_socket]['room']
            file_name = message['file_name']
            file_type = message['file_type']
            file_data = message['file_data']
            file_size = message['file_size']
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            # Store file message
            file_message_data = {
                'username': username,
                'file_name': file_name,
                'file_type': file_type,
                'file_data': file_data,
                'file_size': file_size,
                'timestamp': timestamp
            }
            self.chat_history[room].append(file_message_data)
            
            # Broadcast to room
            broadcast_msg = json.dumps({
                'type': 'file',
                'username': username,
                'file_name': file_name,
                'file_type': file_type,
                'file_data': file_data,
                'file_size': file_size,
                'timestamp': timestamp,
                'room': room
            })
            self.broadcast(broadcast_msg, room, client_socket)
            
            # Save periodically
            if len(self.chat_history[room]) % 10 == 0:
                self.save_chat_history()
                
        except Exception as e:
            if settings.DEBUG:
                print(f"Process file message error: {e}")
    
    def process_chat_message(self, client_socket, message):
        """Process a chat message"""
        try:
            username = self.clients[client_socket]['username']
            room = self.clients[client_socket]['room']
            content = message['content']
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            # Store message
            message_data = {
                'username': username,
                'content': content,
                'timestamp': timestamp
            }
            self.chat_history[room].append(message_data)
            
            # Broadcast to room
            broadcast_msg = json.dumps({
                'type': 'message',
                'username': username,
                'content': content,
                'timestamp': timestamp,
                'room': room
            })
            self.broadcast(broadcast_msg, room, client_socket)
            
            # Save periodically
            if len(self.chat_history[room]) % 10 == 0:
                self.save_chat_history()
                
        except Exception as e:
            if settings.DEBUG:
                print(f"Process chat message error: {e}")
    
    def start(self):
        """Start the server"""
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(settings.MAX_CONNECTIONS)
            print(f"🚀 Chat server started on {self.host}:{self.port}")
            print(f"📝 Available rooms: {list(self.rooms.keys())}")
            
            while True:
                client_socket, address = self.server_socket.accept()
                print(f"🔗 New connection from {address}")
                
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address)
                )
                client_thread.daemon = True
                client_thread.start()
                
        except KeyboardInterrupt:
            print("\n🛑 Server shutting down...")
        except Exception as e:
            print(f"❌ Server error: {e}")
        finally:
            self.server_socket.close()

if __name__ == "__main__":
    server = ChatServer()
    server.start()
