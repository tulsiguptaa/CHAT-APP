import tkinter as tk
from tkinter import messagebox
import json
import os
from config import settings
import bcrypt

# -------- Load & Save User Data -------- #
def load_users():
    if os.path.exists(settings.USER_DB_PATH):
        with open(settings.USER_DB_PATH, 'r') as file:
            return json.load(file)
    return {}

def save_users(users):
    with open(settings.USER_DB_PATH, 'w') as file:
        json.dump(users, file, indent=4)

# -------- Signup Logic -------- #
def signup(username, password):
    users = load_users()
    if username in users:
        return False
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    users[username] = hashed_password.decode('utf-8')  # Store as string
    save_users(users)
    return True

# -------- Login Logic -------- #
def login(username, password):
    users = load_users()
    stored_password = users.get(username)

    if stored_password:
        # Compare entered password with hashed one
        return bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8'))

    return False

# -------- Main GUI Window -------- #
def open_auth_window(start_chat_callback):
    window = tk.Tk()
    window.title(settings.WINDOW_TITLE)
    window.geometry(settings.WINDOW_SIZE)
    window.resizable(False, False)

    # ===== Labels and Entries ===== #
    tk.Label(window, text="Username", font=("Arial", 12)).pack(pady=(20, 5))
    username_entry = tk.Entry(window, font=("Arial", 12))
    username_entry.pack(pady=5)

    tk.Label(window, text="Password", font=("Arial", 12)).pack(pady=5)
    password_entry = tk.Entry(window, show="*", font=("Arial", 12))
    password_entry.pack(pady=5)

    # ===== Actions ===== #
    def handle_login():
        username = username_entry.get()
        password = password_entry.get()

        if login(username, password):
            messagebox.showinfo("Login Successful", f"Welcome {username}!")
            window.destroy()
            start_chat_callback(username)  # Continue to chat window
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")

    def handle_signup():
        username = username_entry.get()
        password = password_entry.get()

        if signup(username, password):
            messagebox.showinfo("Signup Successful", "You can now log in.")
        else:
            messagebox.showerror("Signup Failed", "Username already exists.")

    # ===== Buttons ===== #
    tk.Button(window, text="Login", command=handle_login, font=("Arial", 12)).pack(pady=10)
    tk.Button(window, text="Signup", command=handle_signup, font=("Arial", 12)).pack()

    window.mainloop()
