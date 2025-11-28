import requests
import json
import os
from datetime import datetime

# --- Configuration ---
GIFT_API_URL = "http://cdn.changes.tg/gifts"
DATA_FILE = "gifts_data.json"

# Credentials are read from GitHub Secrets via OS environment variables
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
# ---------------------

def send_telegram_notification(message):
    """Sends a formatted message to the Telegram chat using environment variables."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("ERROR: Telegram credentials not set in environment variables. Notification skipped.")
        return

    # Use the official Telegram Bot API endpoint
    api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'MarkdownV2'
    }

    try:
        response = requests.post(api_url, data=payload)
        response.raise_for_status() 
        print(f"[{datetime.now().isoformat()}] INFO: Telegram notification sent successfully.")
    except requests.exceptions.RequestException as e:
        print(f"[{datetime.now().isoformat()}] ERROR: Failed to send Telegram notification: {e}")

# --- CORRECTED FUNCTION ---
def fetch_current_data(url):
    """Fetches the latest gift data from the API endpoint and handles JSONDecodeError."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status() 
        
        try:
            # Attempt to decode the JSON response
            data = response.json()
            print(f"[{datetime.now().isoformat()}] INFO: Successfully fetched and parsed data.")
            return data
        except json.JSONDecodeError as e:
            # If the data is not JSON (e.g., HTML error page), handle the failure gracefully
            print(f"[{datetime.now().isoformat()}] ERROR: JSON decoding failed. Source returned non-JSON data. Error: {e}")
            print(f"[{datetime.now().isoformat()}] Raw Response Content (First 200 chars): {response.text[:200]}")
            return None 
            
    except requests.exceptions.RequestException as e:
        print(f"[{datetime.now().isoformat()}] ERROR: Network or HTTP failure when fetching data: {e}")
        return None
# --------------------------

def load_previous_data(file_path):
    """Loads the gift data from the local cache file."""
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print(f"[{datetime.now().isoformat()}] ERROR: Could not decode existing data file. Starting fresh.")
                return {}
    print(f"[{datetime.now().isoformat()}] INFO: Previous data file not found. Starting with empty data.")
    return {}

def save_current_data(data, file_path):
    """Saves the latest data to the local cache file."""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"[{datetime.now().isoformat()}] INFO: New data saved to {file_path}.")

def get_gift_keys(data):
    """Extracts the unique identifiers (keys) from the gift data."""
    return set(data.keys())

def main():
    print("--- Telegram Gift Tracker Script Start ---")

    previous_data = load_previous_data(DATA_FILE)
    current_data = fetch_current_data(GIFT_API_URL)

    # If data fetch failed (returned None due to network or JSON error), exit gracefully.
    if current_data is None: 
        print("Script cannot proceed because current data fetch failed. Exiting.")
        return

    previous_keys = get_gift_keys(previous_data)
    current_keys = get_gift_keys(current_data)
    new_gifts = current_keys - previous_keys

    if new_gifts:
        new_gifts_list = '\n'.join([f"• ID: `{gift_id}`" for gift_id in new_gifts])
        
        # Format the message for MarkdownV2 (escaping special characters like '.')
        message = (
            f"🎉 *NEW TELEGRAM GIFTS DETECTED* 🎉\n"
            f"Found {len(new_gifts)} new gift\\(s\\):\n\n"
            f"{new_gifts_list}\n\n"
            f"Check the repository for updated data\\."
        ).replace('.', '\\.') 

        send_telegram_notification(message)
    else:
        print("\n✅ No new gifts detected.")

    # Save the current data for the next run
    save_current_data(current_data, DATA_FILE)
    print("\n--- Telegram Gift Tracker Script End ---")

if __name__ == "__main__":
    main()
