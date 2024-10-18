import json
import os
import time
from helpers.helper import send_email, send_sms
from openaiconfig.openaiservice import get_ai_content
from app import socketio
from threading import Lock

class NotificationManager:
    def __init__(self):
        self.notification_settings_path = os.path.join('storage', 'NotificationSettings.json')
        self.user_accounts_path = os.path.join('storage', 'UserAccounts.json')
        self.lock = Lock()
        self.max_retries = 3
        self.retry_delay = 5  # seconds

    def load_json(self, path):
        with self.lock:
            if not os.path.exists(path):
                with open(path, 'w') as f:
                    json.dump({}, f)
            with open(path, 'r') as f:
                return json.load(f)

    def save_json(self, path, data):
        with self.lock:
            with open(path, 'w') as f:
                json.dump(data, f, indent=4)

    def subscribe_user(self, user_id, bill_id):
        settings = self.load_json(self.notification_settings_path)
        if user_id not in settings:
            settings[user_id] = {"subscriptions": [], "preferences": {}}
        if bill_id not in settings[user_id]["subscriptions"]:
            settings[user_id]["subscriptions"].append(bill_id)
            self.save_json(self.notification_settings_path, settings)
            self.send_confirmation_email(user_id, bill_id)

    def unsubscribe_user(self, user_id, bill_id):
        settings = self.load_json(self.notification_settings_path)
        if user_id in settings and bill_id in settings[user_id]["subscriptions"]:
            settings[user_id]["subscriptions"].remove(bill_id)
            self.save_json(self.notification_settings_path, settings)

    def send_confirmation_email(self, user_id, bill_id):
        user = self.get_user(user_id)
        subject = "Subscription Confirmation"
        body = f"You have successfully subscribed to updates for bill {bill_id}."
        self.retry_send_email(user['email'], subject, body)

    def get_user(self, user_id):
        users = self.load_json(self.user_accounts_path)
        return users.get(str(user_id), {})

    def send_notification(self, user_id, bill_id, message, channels):
        user = self.get_user(user_id)
        if not user:
            return
        preferences = self.get_preferences(user_id)
        for channel in channels:
            if preferences.get(channel, True):
                if channel == 'email':
                    self.retry_send_email(user.get('email'), f"Update on Bill {bill_id}", message)
                elif channel == 'sms':
                    self.retry_send_sms(user.get('phone_number'), message)
                elif channel == 'in_app':
                    self.send_in_app_notification(user_id, message)

    def get_preferences(self, user_id):
        settings = self.load_json(self.notification_settings_path)
        return settings.get(str(user_id), {}).get("preferences", {})

    def manage_preferences(self, user_id, preferences):
        settings = self.load_json(self.notification_settings_path)
        if user_id not in settings:
            settings[user_id] = {"subscriptions": [], "preferences": {}}
        settings[user_id]["preferences"] = preferences
        self.save_json(self.notification_settings_path, settings)

    def retry_send_email(self, email, subject, body):
        for attempt in range(self.max_retries):
            try:
                send_email(email, subject, body)
                return
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    # Log failure or handle accordingly
                    pass

    def retry_send_sms(self, phone_number, message):
        for attempt in range(self.max_retries):
            try:
                send_sms(phone_number, message)
                return
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    # Log failure or handle accordingly
                    pass

    def send_in_app_notification(self, user_id, message):
        socketio.emit('in_app_notification', {'message': message}, room=str(user_id))

notification_manager = NotificationManager()

def trigger_notification(user_id, bill_id, message, channels):
    notification_manager.send_notification(user_id, bill_id, message, channels)

def subscribe(user_id, bill_id):
    notification_manager.subscribe_user(user_id, bill_id)

def unsubscribe(user_id, bill_id):
    notification_manager.unsubscribe_user(user_id, bill_id)

def update_preferences(user_id, preferences):
    notification_manager.manage_preferences(user_id, preferences)

# Example integration with app.py for triggering notifications
# This should be called when a bill status is updated
def on_bill_update(bill_id, update_message):
    settings = notification_manager.load_json(notification_manager.notification_settings_path)
    for user_id, user_settings in settings.items():
        if bill_id in user_settings.get("subscriptions", []):
            channels = []
            if user_settings.get("preferences", {}).get("email", True):
                channels.append('email')
            if user_settings.get("preferences", {}).get("sms", True):
                channels.append('sms')
            if user_settings.get("preferences", {}).get("in_app", True):
                channels.append('in_app')
            notification_manager.send_notification(user_id, bill_id, update_message, channels)

# Ensure that on_bill_update is connected to the relevant event in app.py
socketio.on_event('bill_update', on_bill_update)

# Path: C:\Users\ahmed\GitHub\MYTEGROUP\Backend\notifications.py
# New Script Code is needed.

# End of notifications.py