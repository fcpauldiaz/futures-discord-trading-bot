import re
import hashlib
from typing import Optional, Match
import config

processed_messages = set()

def create_message_id(ticker: str, target_price: float, entry_price: float, profit: float, time_str: str) -> str:
    message_content = f"{ticker}_{target_price}_{entry_price}_{profit}_{time_str}"
    return hashlib.md5(message_content.encode()).hexdigest()

def is_message_processed(message_id: str) -> bool:
    return message_id in processed_messages

def mark_message_processed(message_id: str):
    processed_messages.add(message_id)

def parse_trim_message(content: str) -> Optional[Match]:
    return config.TRIM_PATTERN.search(content)

def parse_stopped_message(content: str) -> Optional[Match]:
    return config.STOPPED_PATTERN.search(content)

def parse_long_triggered_message(content: str) -> Optional[Match]:
    return config.LONG_TRIGGERED_PATTERN.search(content)

def parse_target_hit_message(content: str) -> Optional[Match]:
    return config.TARGET_HIT_PATTERN.search(content)

def parse_target2_hit_message(content: str) -> Optional[Match]:
    return config.TARGET2_HIT_PATTERN.search(content)

def parse_stop_loss_message(content: str) -> Optional[Match]:
    return config.STOP_LOSS_PATTERN.search(content)

def parse_stop_loss_simple_message(content: str) -> Optional[Match]:
    return config.STOP_LOSS_SIMPLE_PATTERN.search(content)

def parse_es_order_message(content: str) -> Optional[Match]:
    return config.PATTERN.search(content)
