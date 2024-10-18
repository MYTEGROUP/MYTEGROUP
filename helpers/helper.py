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
    try:
        with open(filepath, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"The file {filename} does not exist.")
    except json.JSONDecodeError:
        raise ValueError(f"The file {filename} is corrupted.")

# Helper to save data to a JSON file with thread-safe access
def save_json(filename, data):
    filepath = os.path.join(STORAGE_DIR, filename)
    with write_lock:
        try:
            with open(filepath, 'w') as file:
                json.dump(data, file, indent=4)
        except IOError as e:
            raise IOError(f"Failed to write to {filename}: {e}")

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

    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
            server.send_message(msg)
    except smtplib.SMTPException as e:
        raise ConnectionError(f"Failed to send email: {e}")

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
        'comments': [],
        'likes': [],
        'dislikes': [],
        'reports': []
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

# New Utility Functions for Enhanced Features

# Function to like a discussion thread
def like_thread(thread_id, user_id):
    threads = load_json('DiscussionThreads.json')
    for thread in threads:
        if thread['thread_id'] == thread_id:
            if user_id in thread['likes']:
                raise ValueError("User has already liked this thread.")
            thread['likes'].append(user_id)
            # Remove from dislikes if present
            if user_id in thread['dislikes']:
                thread['dislikes'].remove(user_id)
            save_json('DiscussionThreads.json', threads)
            return thread
    raise ValueError("Thread not found.")

# Function to dislike a discussion thread
def dislike_thread(thread_id, user_id):
    threads = load_json('DiscussionThreads.json')
    for thread in threads:
        if thread['thread_id'] == thread_id:
            if user_id in thread['dislikes']:
                raise ValueError("User has already disliked this thread.")
            thread['dislikes'].append(user_id)
            # Remove from likes if present
            if user_id in thread['likes']:
                thread['likes'].remove(user_id)
            save_json('DiscussionThreads.json', threads)
            return thread
    raise ValueError("Thread not found.")

# Function to report inappropriate content in a thread
def report_thread(thread_id, reason, user_id):
    threads = load_json('DiscussionThreads.json')
    for thread in threads:
        if thread['thread_id'] == thread_id:
            report = {
                'report_id': len(thread['reports']) + 1,
                'user_id': user_id,
                'reason': reason
            }
            thread['reports'].append(report)
            save_json('DiscussionThreads.json', threads)
            return thread
    raise ValueError("Thread not found.")

# Function to summarize a discussion thread and store it in SummarizedBills.json
def summarize_discussion(thread_id):
    threads = load_json('DiscussionThreads.json')
    summarized_bills = load_json('SummarizedBills.json')
    for thread in threads:
        if thread['thread_id'] == thread_id:
            summary = get_summary(thread['content'])
            summarized_bills[str(thread_id)] = summary
            save_json('SummarizedBills.json', summarized_bills)
            thread['summary'] = summary
            save_json('DiscussionThreads.json', threads)
            return summary
    raise ValueError("Thread not found.")

# Function to handle replying to a comment within a thread
def reply_to_comment(thread_id, comment_id, reply, user_id):
    threads = load_json('DiscussionThreads.json')
    for thread in threads:
        if thread['thread_id'] == thread_id:
            for comment in thread['comments']:
                if comment['comment_id'] == comment_id:
                    if 'replies' not in comment:
                        comment['replies'] = []
                    comment['replies'].append({
                        'reply_id': len(comment['replies']) + 1,
                        'user_id': user_id,
                        'reply': reply
                    })
                    save_json('DiscussionThreads.json', threads)
                    return thread
            raise ValueError("Comment not found.")
    raise ValueError("Thread not found.")

# Function to like a comment within a thread
def like_comment(thread_id, comment_id, user_id):
    threads = load_json('DiscussionThreads.json')
    for thread in threads:
        if thread['thread_id'] == thread_id:
            for comment in thread['comments']:
                if comment['comment_id'] == comment_id:
                    if 'likes' not in comment:
                        comment['likes'] = []
                    if user_id in comment['likes']:
                        raise ValueError("User has already liked this comment.")
                    comment['likes'].append(user_id)
                    save_json('DiscussionThreads.json', threads)
                    return thread
            raise ValueError("Comment not found.")
    raise ValueError("Thread not found.")

# Function to dislike a comment within a thread
def dislike_comment(thread_id, comment_id, user_id):
    threads = load_json('DiscussionThreads.json')
    for thread in threads:
        if thread['thread_id'] == thread_id:
            for comment in thread['comments']:
                if comment['comment_id'] == comment_id:
                    if 'dislikes' not in comment:
                        comment['dislikes'] = []
                    if user_id in comment['dislikes']:
                        raise ValueError("User has already disliked this comment.")
                    comment['dislikes'].append(user_id)
                    save_json('DiscussionThreads.json', threads)
                    return thread
            raise ValueError("Comment not found.")
    raise ValueError("Thread not found.")

# Function to summarize all discussions and update SummarizedBills.json
def summarize_all_discussions():
    threads = load_json('DiscussionThreads.json')
    summarized_bills = load_json('SummarizedBills.json')
    for thread in threads:
        summary = get_summary(thread['content'])
        summarized_bills[str(thread['thread_id'])] = summary
        thread['summary'] = summary
    save_json('SummarizedBills.json', summarized_bills)
    save_json('DiscussionThreads.json', threads)
    return summarized_bills

# Function to delete a discussion thread (admin functionality)
def delete_discussion_thread(thread_id, admin_id):
    # Placeholder for admin verification logic
    threads = load_json('DiscussionThreads.json')
    for i, thread in enumerate(threads):
        if thread['thread_id'] == thread_id:
            del threads[i]
            save_json('DiscussionThreads.json', threads)
            return {"message": "Thread deleted successfully."}
    raise ValueError("Thread not found.")

# Function to update user notification preferences with validation
def update_notification_preferences(user_id, preferences):
    if not isinstance(preferences, dict):
        raise TypeError("Preferences must be a dictionary.")
    valid_keys = {'email_notifications', 'sms_notifications', 'push_notifications'}
    for key in preferences:
        if key not in valid_keys:
            raise ValueError(f"Invalid preference key: {key}")
        if not isinstance(preferences[key], bool):
            raise ValueError(f"Preference '{key}' must be a boolean.")
    set_user_preferences(user_id, preferences)
    return get_user_preferences(user_id)

# Function to retrieve summarized bill by thread ID
def get_summarized_bill(thread_id):
    summarized_bills = load_json('SummarizedBills.json')
    summary = summarized_bills.get(str(thread_id))
    if summary:
        return summary
    else:
        raise ValueError("Summary not found for the given thread ID.")

# Function to handle reporting inappropriate content in a comment
def report_comment(thread_id, comment_id, reason, user_id):
    threads = load_json('DiscussionThreads.json')
    for thread in threads:
        if thread['thread_id'] == thread_id:
            for comment in thread['comments']:
                if comment['comment_id'] == comment_id:
                    report = {
                        'report_id': len(comment['reports']) + 1,
                        'user_id': user_id,
                        'reason': reason
                    }
                    if 'reports' not in comment:
                        comment['reports'] = []
                    comment['reports'].append(report)
                    save_json('DiscussionThreads.json', threads)
                    return thread
            raise ValueError("Comment not found.")
    raise ValueError("Thread not found.")

# Function to retrieve all reports for administrative review
def get_all_reports():
    threads = load_json('DiscussionThreads.json')
    all_reports = []
    for thread in threads:
        for report in thread.get('reports', []):
            report_info = {
                'thread_id': thread['thread_id'],
                'comment_id': report.get('comment_id'),
                'user_id': report['user_id'],
                'reason': report['reason']
            }
            all_reports.append(report_info)
    return all_reports

# Function to recover from corrupted JSON files
def recover_json(filename, default_data):
    filepath = os.path.join(STORAGE_DIR, filename)
    with write_lock:
        with open(filepath, 'w') as file:
            json.dump(default_data, file, indent=4)
    return default_data

# Error Handling for Missing or Corrupted JSON Files
def safe_load_json(filename):
    try:
        return load_json(filename)
    except (FileNotFoundError, ValueError):
        # Recover with empty list or dict based on expected data structure
        if filename == 'UserAccounts.json' or filename == 'DiscussionThreads.json':
            default_data = []
        elif filename == 'NotificationSettings.json' or filename == 'SummarizedBills.json':
            default_data = {}
        else:
            default_data = {}
        return recover_json(filename, default_data)

# Override load_json with safe_load_json
load_json = safe_load_json

# Function to validate thread existence
def validate_thread_exists(thread_id):
    try:
        get_discussion_thread(thread_id)
    except ValueError:
        raise ValueError("Thread does not exist.")

# Function to validate comment existence
def validate_comment_exists(thread_id, comment_id):
    thread = get_discussion_thread(thread_id)
    for comment in thread['comments']:
        if comment['comment_id'] == comment_id:
            return
    raise ValueError("Comment does not exist.")

# Function to ensure thread-safe operations for complex transactions
def thread_safe_transaction(function, *args, **kwargs):
    with write_lock:
        return function(*args, **kwargs)

# Example usage of thread_safe_transaction
# def safe_like_thread(thread_id, user_id):
#     return thread_safe_transaction(like_thread, thread_id, user_id)

# Additional utility functions can be added below as needed.

# End of helper.py