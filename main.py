import os
import requests
import time 

# --- 1. CONFIGURATION AND SECRETS ---

TELEGRAM_TOKEN = os.getenv('BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')

# Use a TON API provider that offers specific NFT endpoints. 
# tonapi.io is used here for demonstration, but you may need a key for higher limits.
TON_API_BASE_URL = "https://tonapi.io/v2/" 

# **IMPORTANT**: This should be the address of the main NFT Collection or Marketplace Contract.
# Example placeholder for a collection address:
TARGET_ACCOUNT_ADDRESS = "EQA-Q1R35bYd1Gz0N-r2r_tq7fI-W8-e_r_e_r_e_r" # <<< REPLACE THIS!

# File to store the last processed event ID (we now track an item ID or timestamp)
STATE_FILE = 'last_checked_timestamp.txt'


# --- 2. CORE FUNCTIONS ---

def read_last_timestamp():
    """Reads the last known processing timestamp from the state file."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            try:
                # Expecting an integer timestamp (seconds)
                return int(f.read().strip())
            except ValueError:
                return 0
    return 0

def write_last_timestamp(new_timestamp):
    """Writes the new timestamp to the state file."""
    with open(STATE_FILE, 'w') as f:
        f.write(str(new_timestamp))

def send_alert(message_text):
    """Sends a message to the Telegram chat."""
    
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Error: Missing Telegram Token or Chat ID.")
        return

    # Using 'MarkdownV2' for rich formatting
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


def check_for_new_gifts():
    """Fetches NFT transfer events and sends detailed alerts."""
    
    last_timestamp = read_last_timestamp()
    print(f"Last checked timestamp: {last_timestamp}")

    try:
        # Fetch recent NFT transfers related to the collection contract.
        # Filtering by account address requires the specific collection address (e.g., Fragment's).
        # We limit to 10 events to ensure we catch recent drops.
        api_endpoint = f"{TON_API_BASE_URL}nft/transfers?account={TARGET_ACCOUNT_ADDRESS}&limit=10"
        
        response = requests.get(api_endpoint)
        response.raise_for_status()
        data = response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching TON API data: {e}")
        return

    new_events_found = False
    
    # Events are usually returned newest first. We process them oldest first to alert in order.
    transfers = sorted(data.get('nft_transfers', []), key=lambda x: x['block_timestamp'])

    newest_timestamp = last_timestamp

    for transfer in transfers:
        current_timestamp = transfer.get('block_timestamp', 0)
        
        # Skip events that were already processed
        if current_timestamp <= last_timestamp:
            continue
            
        new_events_found = True
        
        # Update the newest timestamp found in this run
        if current_timestamp > newest_timestamp:
            newest_timestamp = current_timestamp

        # --- 3. EXTRACT RICH DETAILS ---
        
        # Get NFT Name and Address
        nft_item = transfer.get('nft_item', {})
        
        # The NFT name is usually in the metadata (though the API sometimes includes it directly)
        item_name = nft_item.get('metadata', {}).get('name', 'Collectible Gift')
        item_address = transfer.get('nft_item_address', 'N/A')
        
        # Format the alert message
        timestamp_readable = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(current_timestamp))
        link = f"https://tonscan.org/nft/{item_address}"
        
        # MarkdownV2 formatting (special characters like '-' and '.' need to be escaped)
        message = (
            f"🎁 *NEW NFT GIFT ALERT\!* 🎁\n\n"
            f"**Item:** `{item_name}`\n"
            f"**Time:** `{timestamp_readable}`\n"
            f"**Source:** `{transfer.get('sender', {}).get('address', 'N/A')[:8]}...`\n"
            f"**Destination:** `{transfer.get('recipient', {}).get('address', 'N/A')[:8]}...`\n"
            f"**Link:** [View Gift]({link})\n"
            f"_Check the link for full details, price, and marketplace\._"
        )
        
        send_alert(message)
        
    # --- 4. STATE UPDATE ---
    
    if new_events_found and newest_timestamp > last_timestamp:
        write_last_timestamp(newest_timestamp)
        print(f"State updated to new timestamp: {newest_timestamp}")
    elif not new_events_found:
        print("No new gifts found since the last check.")


if __name__ == '__main__':
    check_for_new_gifts()
