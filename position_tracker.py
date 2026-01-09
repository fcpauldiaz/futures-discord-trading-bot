import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import config

def save_open_order(order_info: Dict[str, Any]):
    order_data = {
        "timestamp": datetime.now().isoformat(),
        "order_info": order_info
    }
    with open(config.ORDER_FILE, 'w') as f:
        json.dump(order_data, f)

def has_open_order() -> bool:
    if not os.path.exists(config.ORDER_FILE):
        return False
    
    try:
        with open(config.ORDER_FILE, 'r') as f:
            order_data = json.load(f)
        
        order_timestamp = datetime.fromisoformat(order_data["timestamp"])
        if datetime.now() - order_timestamp > timedelta(hours=1):
            clear_open_order()
            return False
        
        return True
    except:
        return False

def clear_open_order():
    if os.path.exists(config.ORDER_FILE):
        os.remove(config.ORDER_FILE)

def get_open_order_info() -> Optional[Dict[str, Any]]:
    if not has_open_order():
        return None
    try:
        with open(config.ORDER_FILE, 'r') as f:
            return json.load(f)
    except:
        return None

def reset_orders_if_expired():
    if has_open_order():
        order_info = get_open_order_info()
        if order_info:
            order_timestamp = datetime.fromisoformat(order_info["timestamp"])
            if datetime.now() - order_timestamp > timedelta(hours=1):
                print("Order expired (1 hour), clearing...")
                clear_open_order()
