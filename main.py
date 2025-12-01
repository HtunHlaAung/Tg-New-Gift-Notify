import os
import requests
import time 

# --- 1. CONFIGURATION AND SECRETS ---

TELEGRAM_TOKEN = os.getenv('BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')

# TON API Configuration (Using a public API for demonstration)
TON_API_URL = "https://tonapi.io/v2/blockchain/accounts/"

# **IMPORTANT**: You must replace this with the actual TON address related to the NFT gifts.
TARGET_ACCOUNT_ADDRESS = "EQC_f3_s-43y5xW5-K7wQh-Yy9P0I_q-456g-G-H-I-J-K" # <<< REPLACE THIS!

# File to store the last processed transaction hash (for state management)
STATE_FILE = 'last_checked_hash.txt'


# --- 2. CORE FUNCTIONS ---

def read_last_hash():
    """Reads the last known transaction hash from the state file."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return f.read().strip()
    return None

def write_last_hash(new_hash):
    """Writes the new transaction hash to the state file."""
    with open(STATE_FILE, 'w') as f:
        f.write(new_hash)

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
        print(f"Response body: {response.text if response is not None else 'No response'}")


def check_for_new_gifts():
    """The main logic to check for new NFT transfers and send alerts."""
    
    last_hash = read_last_hash()
    print(f"Last checked transaction hash: {last_hash}")

    try:
        # Fetch the latest transactions for the target account
        api_endpoint = f"{TON_API_URL}{TARGET_ACCOUNT_ADDRESS}/transactions?limit=5"
        
        response = requests.get(api_endpoint)
        response.raise_for_status()
        data = response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching TON API data: {e}")
        return

    new_gifts_found = False
    latest_hash = None
    
    transactions = data.get('transactions', [])
    
    # If this is the first run, only set the state and don't send massive alerts
    if last_hash is None and transactions:
        latest_hash = transactions[0].get('hash')
        write_last_hash(latest_hash)
        print(f"First run. State initialized to hash: {latest_hash}")
        return

    # Iterate through transactions to find new ones
    for tx in transactions:
        tx_hash = tx.get('hash')
        
        if tx_hash == last_hash:
            break
        
        if latest_hash is None:
            latest_hash = tx_hash

        new_gifts_found = True
        
        # Format the alert message (MarkdownV2 requires escaping special characters)
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(tx.get('now')))
        
        # Link example:
        link = f"https://tonscan.org/tx/{tx_hash}" 
        
        message = (
            f"🎁 *NEW NFT GIFT ALERT\!* 🎁\n\n"
            f"**Time:** `{timestamp}`\n"
            f"**Transaction:** [`{tx_hash}`]({link})\n"
            f"**Account:** `{TARGET_ACCOUNT_ADDRESS[:8]}...`\n\n"
            f"_Check the link for details\._"
        )
        
        send_alert(message)
        
    # --- 3. STATE UPDATE ---
    
    if new_gifts_found and latest_hash:
        write_last_hash(latest_hash)
        print(f"State updated to new hash: {latest_hash}")
    elif not new_gifts_found:
        print("No new gifts found since the last check.")


if __name__ == '__main__':
    check_for_new_gifts()
