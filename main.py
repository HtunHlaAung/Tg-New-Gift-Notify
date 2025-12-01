import os
import requests
import json

# --- 1. CONFIGURATION AND SECRETS ---

# Telegram Secrets (Read from GitHub Actions Environment Variables)
TELEGRAM_TOKEN = os.getenv('BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')

# TON API Configuration (Using a public API for demonstration)
# NOTE: Replace with a more stable, production API endpoint if you run into rate limits.
TON_API_URL = "https://tonapi.io/v2/blockchain/accounts/"

# The address of the TON account (or collection contract) you want to monitor.
# **IMPORTANT**: You must replace this with the actual TON address related to the NFT gifts.
# This example uses a common NFT Collection address for demonstration purposes.
TARGET_ACCOUNT_ADDRESS = "EQC_f3_s-43y5xW5-K7wQh-Yy9P0I_q-456g-G-H-I-J-K" # <<< REPLACE THIS!

# File to store the last processed transaction hash (for state management on GitHub Actions)
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
        # We look for only a few (limit=5) transactions and order by time (desc)
        api_endpoint = f"{TON_API_URL}{TARGET_ACCOUNT_ADDRESS}/transactions?limit=5"
        
        # NOTE: You may need to pass the TON_API_KEY in the headers for some providers.
        # headers = {'Authorization': f'Bearer {os.getenv("TON_API_KEY")}'}
        response = requests.get(api_endpoint)
        response.raise_for_status()
        data = response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching TON API data: {e}")
        return

    new_gifts_found = False
    
    # TON API returns a list of transactions (hashes, lt, etc.)
    # The actual "gift" or NFT transfer logic often requires deeper parsing (not possible with this generic API endpoint).
    # **For a real NFT gift bot**, you would use a specialized API endpoint like `nft/transfers` 
    # and filter for transactions involving known gift/collection addresses.
    
    # --- SIMPLIFIED MONITORING LOGIC (Using basic transaction hash) ---
    
    latest_hash = None
    
    for tx in data.get('transactions', []):
        tx_hash = tx.get('hash')
        
        if tx_hash == last_hash:
            break  # Stop processing once we hit the last known transaction
        
        if latest_hash is None:
            latest_hash = tx_hash

        # Assume every transaction is a 'gift' for this example. 
        # In reality, you'd check message contents or specific collection IDs.
        
        new_gifts_found = True
        
        # Format the alert message
        # Telegram MarkdownV2 requires special characters to be escaped.
        name = f"Telegram Collectible Gift \\(TX: {tx_hash[:6]}...\\)"
        link = f"https://tonscan.org/tx/{tx_hash}" 
        
        message = (
            f"🎁 *NEW NFT GIFT ALERT\!* 🎁\n\n"
            f"**Item:** {name}\n"
            f"**Transaction:** [`{tx_hash}`]({link})\n"
            f"**Account Monitored:** `{TARGET_ACCOUNT_ADDRESS[:8]}...`\n\n"
            f"_Check the link above for details\._"
        )
        
        send_alert(message)
        
    # --- 3. STATE UPDATE ---
    
    if new_gifts_found and latest_hash:
        write_last_hash(latest_hash)
        print(f"State updated to new hash: {latest_hash}")
    elif not new_gifts_found:
        print("No new gifts found since the last check.")


if __name__ == '__main__':
    # Ensure the script runs the core function
    check_for_new_gifts()
