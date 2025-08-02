import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
from datetime import datetime
import os
import base64
from PIL import Image, ImageTk
from io import BytesIO
from client.client import ChatClient
from config import settings

class ChatGUI:
    def __init__(self, username):
        self.username = username
        self.client = None
        self.current_room = 'general'
        self.rooms = ['general', 'random', 'tech', 'gaming']
        
        # Create main window
        self.root = tk.Tk()
        self.root.title(f"Chat App - {username}")
        self.root.geometry("900x600")
        self.root.configure(bg='#2c3e50')
        
        # Configure grid weights
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        
        self.setup_ui()
        self.connect_to_server()
    
    def setup_ui(self):
        # Left sidebar
        self.setup_sidebar()
        
        # Main chat area
        self.setup_chat_area()
        
        # Status bar
        self.setup_status_bar()
    
    def setup_sidebar(self):
        sidebar = tk.Frame(self.root, bg='#34495e', width=250)
        sidebar.grid(row=0, column=0, sticky='nsew', padx=2, pady=2)
        sidebar.grid_propagate(False)
        
        # User info
        user_frame = tk.Frame(sidebar, bg='#34495e')
        user_frame.pack(fill='x', padx=15, pady=15)
        
        tk.Label(user_frame, text=f"👤 {self.username}", 
                font=('Arial', 14, 'bold'), 
                bg='#34495e', fg='white').pack()
        
        # Room selection
        room_frame = tk.Frame(sidebar, bg='#34495e')
        room_frame.pack(fill='x', padx=15, pady=15)
        
        tk.Label(room_frame, text="📝 Chat Rooms", 
                font=('Arial', 12, 'bold'), 
                bg='#34495e', fg='white').pack(anchor='w')
        
        self.room_var = tk.StringVar(value=self.current_room)
        for room in self.rooms:
            room_btn = tk.Radiobutton(room_frame, text=f"# {room.title()}", 
                                    variable=self.room_var, value=room,
                                    command=self.change_room,
                                    font=('Arial', 10),
                                    bg='#34495e', fg='white', 
                                    selectcolor='#2c3e50',
                                    activebackground='#34495e',
                                    activeforeground='#3498db')
            room_btn.pack(anchor='w', pady=3)
        
        # Disconnect button
        disconnect_btn = tk.Button(sidebar, text="🚪 Disconnect", 
                                 command=self.disconnect,
                                 font=('Arial', 11),
                                 bg='#e74c3c', fg='white',
                                 activebackground='#c0392b',
                                 borderwidth=0, padx=20, pady=8)
        disconnect_btn.pack(pady=15)
    
    def setup_chat_area(self):
        chat_frame = tk.Frame(self.root, bg='#2c3e50')
        chat_frame.grid(row=0, column=1, sticky='nsew', padx=2, pady=2)
        chat_frame.grid_rowconfigure(0, weight=1)
        chat_frame.grid_columnconfigure(0, weight=1)
        
        # Chat display
        self.chat_display = scrolledtext.ScrolledText(
            chat_frame, bg='#ecf0f1', fg='#2c3e50',
            font=('Consolas', 11), wrap=tk.WORD,
            state='disabled', borderwidth=0
        )
        self.chat_display.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        
        # Message input area
        input_frame = tk.Frame(chat_frame, bg='#2c3e50')
        input_frame.grid(row=1, column=0, sticky='ew', padx=5, pady=5)
        input_frame.grid_columnconfigure(0, weight=1)
        
        self.message_entry = tk.Entry(input_frame, font=('Arial', 12),
                                    bg='#ecf0f1', fg='#2c3e50',
                                    borderwidth=0, relief='flat')
        self.message_entry.grid(row=0, column=0, sticky='ew', padx=(0, 10))
        self.message_entry.bind('<Return>', self.send_message)
        
        # File attachment button
        attach_btn = tk.Button(input_frame, text="📎", 
                             command=self.attach_file,
                             font=('Arial', 12),
                             bg='#95a5a6', fg='white',
                             activebackground='#7f8c8d',
                             activeforeground='white',
                             borderwidth=0, padx=12, pady=8,
                             cursor='hand2', relief='flat')
        attach_btn.grid(row=0, column=1, padx=(0, 10))
        
        # Hover effects for attach button
        attach_btn.bind('<Enter>', lambda e: attach_btn.configure(bg='#7f8c8d'))
        attach_btn.bind('<Leave>', lambda e: attach_btn.configure(bg='#95a5a6'))
        
        send_btn = tk.Button(input_frame, text="📤 Send", 
                           command=self.send_message,
                           font=('Arial', 11),
                           bg='#3498db', fg='white',
                           activebackground='#2980b9',
                           borderwidth=0, padx=15, pady=8)
        send_btn.grid(row=0, column=2)
    
    def setup_status_bar(self):
        self.status_bar = tk.Label(self.root, text="Connecting...", 
                                 font=('Arial', 9),
                                 bg='#34495e', fg='white',
                                 anchor='w', relief='sunken')
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky='ew')
    
    def connect_to_server(self):
        def connect():
            self.client = ChatClient(self.username, self.current_room)
            self.client.set_message_callback(self.handle_message)
            self.client.set_status_callback(self.update_status)
            
            if self.client.connect():
                self.update_status("Connected")
                self.add_system_message("Connected to chat server!")
            else:
                self.update_status("Connection failed")
                messagebox.showerror("Connection Error", 
                                   "Failed to connect to server. Please try again.")
        
        connect_thread = threading.Thread(target=connect)
        connect_thread.daemon = True
        connect_thread.start()
    
    def handle_message(self, message):
        msg_type = message.get('type')
        
        if msg_type == 'message':
            username = message['username']
            content = message['content']
            timestamp = message['timestamp']
            
            if username == self.username:
                self.add_message(f"You: {content}", timestamp, is_own=True)
            else:
                self.add_message(f"{username}: {content}", timestamp)
        
        elif msg_type == 'file':
            username = message['username']
            file_name = message['file_name']
            file_type = message['file_type']
            file_data = message['file_data']
            timestamp = message['timestamp']
            
            if username == self.username:
                self.add_file_message(f"You sent: {file_name}", file_type, file_data, timestamp, is_own=True)
            else:
                self.add_file_message(f"{username} sent: {file_name}", file_type, file_data, timestamp)
        
        elif msg_type == 'user_joined':
            username = message['username']
            self.add_system_message(f"{username} joined the room")
        
        elif msg_type == 'user_left':
            username = message['username']
            self.add_system_message(f"{username} left the room")
        
        elif msg_type == 'history':
            messages = message['messages']
            self.chat_display.config(state='normal')
            self.chat_display.delete(1.0, tk.END)
            self.chat_display.config(state='disabled')
            
            for msg in messages:
                username = msg['username']
                content = msg['content']
                timestamp = msg['timestamp']
                
                if username == self.username:
                    self.add_message(f"You: {content}", timestamp, is_own=True)
                else:
                    self.add_message(f"{username}: {content}", timestamp)
    
    def add_message(self, text, timestamp, is_own=False):
        self.chat_display.config(state='normal')
        
        # Add timestamp
        self.chat_display.insert(tk.END, f"[{timestamp}] ", 'timestamp')
        
        # Add message with different color for own messages
        if is_own:
            self.chat_display.insert(tk.END, f"{text}\n", 'own_message')
        else:
            self.chat_display.insert(tk.END, f"{text}\n", 'message')
        
        self.chat_display.config(state='disabled')
        self.chat_display.see(tk.END)
        
        # Configure tags for colors
        self.chat_display.tag_config('timestamp', foreground='#7f8c8d')
        self.chat_display.tag_config('message', foreground='#2c3e50')
        self.chat_display.tag_config('own_message', foreground='#27ae60')
    
    def add_system_message(self, text):
        self.chat_display.config(state='normal')
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.chat_display.insert(tk.END, f"[{timestamp}] {text}\n", 'system')
        self.chat_display.config(state='disabled')
        self.chat_display.see(tk.END)
        
        # Configure system message color
        self.chat_display.tag_config('system', foreground='#e67e22')
    
    def add_file_message(self, text, file_type, file_data, timestamp, is_own=False):
        """Add a file message to the chat display"""
        self.chat_display.config(state='normal')
        
        # Add timestamp
        self.chat_display.insert(tk.END, f"[{timestamp}] ", 'timestamp')
        
        # Add file message with different color for own messages
        if is_own:
            self.chat_display.insert(tk.END, f"{text}\n", 'own_message')
        else:
            self.chat_display.insert(tk.END, f"{text}\n", 'message')
        
        # Add file type indicator
        file_icons = {
            'image': '🖼️',
            'document': '📄',
            'video': '🎥',
            'audio': '🎵',
            'file': '📎'
        }
        
        icon = file_icons.get(file_type, '📎')
        self.chat_display.insert(tk.END, f"  {icon} {file_type.upper()} file\n", 'file_message')
        
        # Add download button text
        self.chat_display.insert(tk.END, "  [Click to download]\n", 'download_link')
        
        self.chat_display.config(state='disabled')
        self.chat_display.see(tk.END)
        
        # Configure file message styling
        self.chat_display.tag_config('file_message', foreground='#3498db', font=('Arial', 10, 'bold'))
        self.chat_display.tag_config('download_link', foreground='#e74c3c', font=('Arial', 9, 'underline'))
        
        # Bind click event for download
        self.chat_display.tag_bind('download_link', '<Button-1>', 
                                 lambda e, data=file_data, name=text.split(': ')[-1]: 
                                 self.download_file(data, name))
    
    def download_file(self, file_data, file_name):
        """Download and save a file"""
        try:
            # Decode base64 data
            file_bytes = base64.b64decode(file_data)
            
            # Ask user where to save the file
            save_path = filedialog.asksaveasfilename(
                title="Save file as",
                initialvalue=file_name,
                defaultextension=os.path.splitext(file_name)[1]
            )
            
            if save_path:
                with open(save_path, 'wb') as file:
                    file.write(file_bytes)
                messagebox.showinfo("Success", f"File saved as: {save_path}")
            else:
                messagebox.showinfo("Cancelled", "File download cancelled")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to download file: {str(e)}")
    
    def attach_file(self):
        """Open file dialog to select and send files"""
        file_path = filedialog.askopenfilename(
            title="Select file to send",
            filetypes=[
                ("All files", "*.*"),
                ("Images", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("Documents", "*.pdf *.doc *.docx *.txt"),
                ("Videos", "*.mp4 *.avi *.mov"),
                ("Audio", "*.mp3 *.wav *.flac")
            ]
        )
        
        if file_path:
            self.send_file(file_path)
    
    def send_file(self, file_path):
        """Send a file to the chat"""
        try:
            file_size = os.path.getsize(file_path)
            max_size = 10 * 1024 * 1024  # 10MB limit
            
            if file_size > max_size:
                messagebox.showerror("File too large", "File size must be less than 10MB")
                return
            
            # Get file info
            file_name = os.path.basename(file_path)
            file_ext = os.path.splitext(file_name)[1].lower()
            
            # Determine file type
            if file_ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
                file_type = 'image'
            elif file_ext in ['.pdf', '.doc', '.docx', '.txt']:
                file_type = 'document'
            elif file_ext in ['.mp4', '.avi', '.mov']:
                file_type = 'video'
            elif file_ext in ['.mp3', '.wav', '.flac']:
                file_type = 'audio'
            else:
                file_type = 'file'
            
            # Show progress message
            self.add_system_message(f"📤 Sending file: {file_name}...")
            
            # Start file transfer in separate thread
            transfer_thread = threading.Thread(
                target=self._send_file_thread,
                args=(file_path, file_name, file_type, file_size)
            )
            transfer_thread.daemon = True
            transfer_thread.start()
                
        except Exception as e:
            self.add_system_message(f"❌ Error preparing file: {str(e)}")
            messagebox.showerror("Error", f"Failed to prepare file: {str(e)}")
    
    def _send_file_thread(self, file_path, file_name, file_type, file_size):
        """Send file in a separate thread to avoid GUI freezing"""
        try:
            # Read file and encode as base64
            with open(file_path, 'rb') as file:
                file_data = file.read()
                file_base64 = base64.b64encode(file_data).decode('utf-8')
            
            # Send file message
            if self.client and self.client.connected:
                file_message = {
                    'type': 'file',
                    'file_name': file_name,
                    'file_type': file_type,
                    'file_data': file_base64,
                    'file_size': file_size
                }
                
                if self.client.send_file_message(file_message):
                    # Update GUI from main thread
                    self.root.after(0, lambda: self.add_system_message(f"✅ File sent successfully: {file_name}"))
                else:
                    # Update GUI from main thread
                    self.root.after(0, lambda: self.add_system_message(f"❌ Failed to send file: {file_name}"))
                    self.root.after(0, lambda: messagebox.showerror("Error", "Failed to send file"))
            else:
                # Update GUI from main thread
                self.root.after(0, lambda: messagebox.showerror("Error", "Not connected to server"))
                
        except Exception as e:
            # Update GUI from main thread
            self.root.after(0, lambda: self.add_system_message(f"❌ Error sending file: {str(e)}"))
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to send file: {str(e)}"))
    
    def send_message(self, event=None):
        content = self.message_entry.get().strip()
        if content and self.client and self.client.connected:
            if self.client.send_chat_message(content):
                self.message_entry.delete(0, tk.END)
            else:
                messagebox.showerror("Error", "Failed to send message")
    
    def change_room(self):
        new_room = self.room_var.get()
        if new_room != self.current_room and self.client:
            if self.client.change_room(new_room):
                self.current_room = new_room
                self.add_system_message(f"Switched to #{new_room} room")
            else:
                messagebox.showerror("Error", "Failed to change room")
    
    def update_status(self, status):
        self.status_bar.config(text=f"Status: {status}")
    
    def disconnect(self):
        if self.client:
            self.client.disconnect()
        self.root.quit()
    
    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.disconnect)
        self.root.mainloop()

def open_chat_window(username):
    chat_gui = ChatGUI(username)
    chat_gui.run() 