import requests
import hashlib
from typing import Optional, Dict, Any
import config

processed_discord_messages = set()
logged_invalid_messages = set()

def get_headers(token: str) -> Dict[str, str]:
    return {"Authorization": token}

def fetch_last_message(channel_id: Optional[str] = None, token: Optional[str] = None) -> Optional[Dict[str, Any]]:
    token = token or config.TOKEN
    channel_id = channel_id or config.CHANNEL_ID
    api_url = f"https://discord.com/api/v10/channels/{channel_id}/messages?limit=1"
    
    try:
        response = requests.get(api_url, headers=get_headers(token))
        response.raise_for_status()
        messages = response.json()
        if not messages:
            return None
        return messages[0]
    except Exception as e:
        print(f"Error fetching message from channel {channel_id}: {e}")
        return None

def fetch_second_channel_messages(limit: int = 2) -> Optional[list]:
    try:
        headers = get_headers(config.TOKEN_2)
        response = requests.get(config.API_URL_2, headers=headers)
        response.raise_for_status()
        messages = response.json()
        if not messages:
            return None
        return messages
    except Exception as e:
        print(f"Error fetching messages from second channel: {e}")
        return None

def is_discord_message_processed(msg_id: str) -> bool:
    return msg_id in processed_discord_messages

def mark_discord_message_processed(msg_id: str):
    processed_discord_messages.add(msg_id)

def is_invalid_message_logged(msg_id: Optional[str], content: str = "") -> bool:
    identifier = msg_id if msg_id else hashlib.md5(content.encode()).hexdigest()
    return identifier in logged_invalid_messages

def mark_invalid_message_logged(msg_id: Optional[str], content: str = ""):
    identifier = msg_id if msg_id else hashlib.md5(content.encode()).hexdigest()
    logged_invalid_messages.add(identifier)
