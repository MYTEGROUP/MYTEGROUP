# helpers/helper.py

import json
import os
from config import STORAGE_DIR, EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD
from threading import Lock
import bcrypt
import smtplib
from email.message import EmailMessage
from openaiconfig.openaiservice import get_summary

# Lock to prevent race conditions during file writes
write_lock = Lock()

# Helper to load data from a JSON file
def load_json(filename):
    filepath = os.path.join(STORAGE_DIR, filename)
    with open(filepath, 'r') as file:
        return json.load(file)

# Helper to save data to a JSON file with thread-safe access
def save_json(filename, data):
    filepath = os.path.join(STORAGE_DIR, filename)
    with write_lock:
        with open(filepath, 'w') as file:
            json.dump(data, file, indent=4)

# Utility function for hashing passwords
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Utility function for verifying passwords
def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# Utility function for sending emails
def send_email(to_email, subject, body):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = EMAIL_HOST_USER
    msg['To'] = to_email
    msg.set_content(body)

    with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
        server.starttls()
        server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
        server.send_message(msg)

# User Authentication Functions

def register(username, email, password):
    users = load_json('UserAccounts.json')
    # Check if username or email already exists
    for user in users:
        if user['username'] == username:
            raise ValueError("Username already exists.")
        if user['email'] == email:
            raise ValueError("Email already registered.")
    # Hash the password
    hashed_pw = hash_password(password)
    # Create new user entry
    new_user = {
        'id': len(users) + 1,
        'username': username,
        'email': email,
        'password': hashed_pw
    }
    users.append(new_user)
    save_json('UserAccounts.json', users)
    # Send confirmation email
    subject = "Registration Successful"
    body = f"Hello {username},\n\nYour registration was successful."
    send_email(email, subject, body)
    return new_user

def login(username, password):
    users = load_json('UserAccounts.json')
    for user in users:
        if user['username'] == username:
            if verify_password(password, user['password']):
                # In a real application, you would generate and return a session token
                return {"message": "Login successful", "user_id": user['id']}
            else:
                raise ValueError("Incorrect password.")
    raise ValueError("Username not found.")

def logout(session_token):
    # Placeholder for session management logic
    # This would involve invalidating the session token
    return {"message": "Logout successful"}

# User Preferences Management

def get_user_preferences(user_id):
    preferences = load_json('NotificationSettings.json')
    return preferences.get(str(user_id), {})

def set_user_preferences(user_id, preferences):
    all_preferences = load_json('NotificationSettings.json')
    all_preferences[str(user_id)] = preferences
    save_json('NotificationSettings.json', all_preferences)

# Notification Handling

def send_notification(user_id, subject, message):
    preferences = get_user_preferences(user_id)
    if preferences.get('email_notifications', False):
        users = load_json('UserAccounts.json')
        user_email = None
        for user in users:
            if user['id'] == user_id:
                user_email = user['email']
                break
        if user_email:
            send_email(user_email, subject, message)

# Discussion Threads Management

def create_discussion_thread(title, content, user_id):
    threads = load_json('DiscussionThreads.json')
    summary = get_summary(content)
    new_thread = {
        'thread_id': len(threads) + 1,
        'title': title,
        'content': content,
        'summary': summary,
        'created_by': user_id,
        'comments': []
    }
    threads.append(new_thread)
    save_json('DiscussionThreads.json', threads)
    return new_thread

def get_discussion_threads():
    return load_json('DiscussionThreads.json')

def get_discussion_thread(thread_id):
    threads = load_json('DiscussionThreads.json')
    for thread in threads:
        if thread['thread_id'] == thread_id:
            return thread
    raise ValueError("Thread not found.")

def update_discussion_thread(thread_id, new_content):
    threads = load_json('DiscussionThreads.json')
    for thread in threads:
        if thread['thread_id'] == thread_id:
            thread['content'] = new_content
            thread['summary'] = get_summary(new_content)
            save_json('DiscussionThreads.json', threads)
            return thread
    raise ValueError("Thread not found.")

def add_comment_to_thread(thread_id, comment, user_id):
    threads = load_json('DiscussionThreads.json')
    for thread in threads:
        if thread['thread_id'] == thread_id:
            thread['comments'].append({
                'comment_id': len(thread['comments']) + 1,
                'user_id': user_id,
                'comment': comment
            })
            save_json('DiscussionThreads.json', threads)
            return thread
    raise ValueError("Thread not found.")
```