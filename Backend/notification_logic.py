import asyncio
import json
import os
from typing import List, Dict
from helpers.helper import send_email, send_sms, send_in_app_notification
from Backend import notifications

USER_ACCOUNTS_PATH = os.path.join('storage', 'UserAccounts.json')
NOTIFICATION_SETTINGS_PATH = os.path.join('storage', 'NotificationSettings.json')
BILLS_PATH = os.path.join('storage', 'CanadaBills.json')
BILLS_ENHANCED_PATH = os.path.join('storage', 'CanadaBillsEnhanced.json')
SUMMARIZED_BILLS_PATH = os.path.join('storage', 'SummarizedBills.json')

MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

async def load_json(filepath: str) -> Dict:
    """Load JSON data from a file."""
    try:
        with open(filepath, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def get_updated_bills() -> List[Dict]:
    """
    Determine which bills have been updated.
    This function should be implemented to detect updates to parliamentary bills.
    For demonstration, it returns an empty list.
    """
    # Placeholder for bill update detection logic
    return []

def get_subscribed_users(updated_bills: List[Dict], user_accounts: Dict, notification_settings: Dict) -> List[Dict]:
    """Retrieve users subscribed to updates for the given bills."""
    subscribed_users = []
    for bill in updated_bills:
        bill_id = bill.get('id')
        for user_id, preferences in notification_settings.items():
            if bill_id in preferences.get('subscribed_bills', []):
                user_info = user_accounts.get(user_id)
                if user_info:
                    subscribed_users.append({
                        'user_id': user_id,
                        'email': user_info.get('email'),
                        'phone': user_info.get('phone'),
                        'preferences': preferences
                    })
    return subscribed_users

def format_notification(user: Dict, bill: Dict) -> str:
    """Format the notification content based on user preferences and bill updates."""
    title = bill.get('title', 'a bill')
    status = bill.get('status', 'updated')
    link = bill.get('link', '#')
    personalized_content = f"Hello {user['user_id']}, the bill '{title}' has been {status}. More details here: {link}"
    return personalized_content

async def send_with_retry(send_func, *args, **kwargs):
    """Send a notification with retry mechanism."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            await send_func(*args, **kwargs)
            return
        except Exception as e:
            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_DELAY)
            else:
                print(f"Failed to send notification after {MAX_RETRIES} attempts: {e}")

async def send_notifications(user: Dict, bill: Dict):
    """Send notifications via preferred methods."""
    content = format_notification(user, bill)
    tasks = []
    preferences = user.get('preferences', {})
    
    if preferences.get('email', False):
        tasks.append(send_with_retry(send_email, user['email'], content))
    if preferences.get('sms', False):
        tasks.append(send_with_retry(send_sms, user['phone'], content))
    if preferences.get('in_app', False):
        tasks.append(send_with_retry(send_in_app_notification, user['user_id'], content))
    
    await asyncio.gather(*tasks)

async def process_notifications():
    """Main process to handle notification logic."""
    user_accounts = await load_json(USER_ACCOUNTS_PATH)
    notification_settings = await load_json(NOTIFICATION_SETTINGS_PATH)
    updated_bills = get_updated_bills()
    
    if not updated_bills:
        return
    
    subscribed_users = get_subscribed_users(updated_bills, user_accounts, notification_settings)
    
    tasks = []
    for bill in updated_bills:
        for user in subscribed_users:
            tasks.append(send_notifications(user, bill))
    
    await asyncio.gather(*tasks)

async def main():
    """Entry point for the notification logic."""
    while True:
        await process_notifications()
        await asyncio.sleep(60)  # Check for updates every 60 seconds

if __name__ == "__main__":
    asyncio.run(main())
    
# Helper functions should handle actual sending and error management
# notifications.py should include necessary functions to interface with different delivery methods

# End of Backend/notification_logic.py