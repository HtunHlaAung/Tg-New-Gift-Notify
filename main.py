import os
import requests
import time 

# --- 1. CONFIGURATION AND SECRETS ---

# This version ignores the TON API key and state file, only focusing on Telegram.
TELEGRAM_TOKEN = os.getenv('BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')


# --- 2. CORE FUNCTIONS ---

def send_alert(message_text):
    """Sends a message to the Telegram chat."""
    
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Error: Missing Telegram Token or Chat ID.")
        return

    # Use 'MarkdownV2' for better formatting, ensuring proper escaping.
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message_text,
        'parse_mode': 'MarkdownV2'
    }
    
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        print("Alert sent successfully!")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send alert: {e}")
        # Note: In a test environment, you want the full error:
        print(f"Response body: {response.text if response is not None else 'No response'}")


def run_test_alert():
    """Generates and sends a single, unique test alert."""
    
    current_time = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    
    # Message using MarkdownV2 syntax
    message = (
        f"🚨 *BOT TEST SUCCESSFUL\!* 🚨\n\n"
        f"This confirms your Telegram configuration is working\\.\n"
        f"**Test Time:** `{current_time}`\n"
        f"_Please revert main\\.py to the monitoring version\\._"
    )
    
    send_alert(message)
    print("Test finished. Telegram alert should be visible.")


if __name__ == '__main__':
    run_test_alert()
