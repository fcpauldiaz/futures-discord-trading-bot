import requests
import time
from typing import Dict, List, Optional, Union
import config

def send_ntfy_notification(payload: Dict, quantity: Optional[int], operation_name: str, additional_context: Optional[Dict] = None):
    try:
        ticker = payload.get("ticker", "Unknown")
        action = payload.get("action", "Unknown")
        price = payload.get("price", "")
        order_type = payload.get("orderType", "market")
        
        qty = quantity if quantity is not None else payload.get("quantity", "Unknown")
        
        title = f"Order Placed: {ticker} {action.upper()}"
        
        message_parts = [
            f"Ticker: {ticker}",
            f"Action: {action.upper()}",
            f"Quantity: {qty}",
        ]
        
        if price:
            message_parts.append(f"Price: {price}")
        
        if order_type and order_type != "market":
            message_parts.append(f"Order Type: {order_type}")
        
        if additional_context:
            source = additional_context.get("source")
            if source:
                message_parts.append(f"Source: {source}")
            
            direction = additional_context.get("direction")
            if direction:
                message_parts.append(f"Direction: {direction}")
            
            letter = additional_context.get("letter")
            if letter:
                message_parts.append(f"Letter: {letter}")
            
            score = additional_context.get("score")
            if score:
                message_parts.append(f"Score: {score}")
            
            level = additional_context.get("level")
            if level:
                message_parts.append(f"Level: {level}")
            
            interval = additional_context.get("interval")
            if interval:
                message_parts.append(f"Interval: {interval}")
            
            stop_value = additional_context.get("stop_value")
            if stop_value:
                message_parts.append(f"Stop: {stop_value}")
        
        message_parts.append(f"Operation: {operation_name}")
        
        message = "\n".join(message_parts)
        
        ntfy_url = "https://ntfy.sh/fcpauldiaz_notifications"
        headers = {
            "Title": title,
            "Priority": "default",
            "Tags": "chart_with_upwards_trend"
        }
        
        requests.post(ntfy_url, data=message.encode("utf-8"), headers=headers, timeout=5)
        print(f"ntfy notification sent: {title}")
    except Exception as e:
        print(f"Error sending ntfy notification: {e}")

def send_webhook(
    payload: Dict,
    url: str,
    quantity: Optional[int] = None,
    operation_name: str = "webhook",
    is_entry_trade: bool = False,
    additional_context: Optional[Dict] = None
):
    if not url:
        print(f"No URL provided for {operation_name}")
        return
    
    webhook_payload = payload.copy()
    if quantity is not None:
        webhook_payload["quantity"] = quantity
    elif "quantity" not in webhook_payload:
        webhook_payload["quantity"] = config.GLOBAL_QUANTITY
    
    for attempt in range(5):
        try:
            webhook_response = requests.post(url, json=webhook_payload)
            webhook_response.raise_for_status()
            qty_info = f" (qty: {webhook_payload.get('quantity')})"
            print(f"{operation_name} submitted successfully to {url}{qty_info} (attempt {attempt + 1})")
            if is_entry_trade:
                send_ntfy_notification(webhook_payload, quantity, operation_name, additional_context)
            break
        except Exception as e:
            print(f"Error submitting {operation_name} to {url} (attempt {attempt + 1}): {e}")
            if attempt < 4:
                time.sleep(1)
            else:
                print(f"{operation_name} failed after all retries for {url}")

def send_webhook_to_multiple_urls(
    payload: Dict,
    urls: Union[List[str], str],
    operation_name: str = "webhook",
    quantity: Optional[int] = None,
    is_entry_trade: bool = False,
    additional_context: Optional[Dict] = None
):
    if isinstance(urls, str):
        urls = [urls]
    
    if not urls:
        print(f"No URLs provided for {operation_name}")
        return
    
    for url in urls:
        send_webhook(payload, url, quantity, operation_name, is_entry_trade, additional_context)
