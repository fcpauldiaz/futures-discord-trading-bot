import time
from datetime import datetime
import config
import discord_scraper
import message_parser
import order_executor
import position_tracker

def is_weekday() -> bool:
    return datetime.now().weekday() < 5

def handle_trim_message(trim_match):
    if not position_tracker.has_open_order():
        print("No open order to trim")
        return
    
    order_info = position_tracker.get_open_order_info()
    if not order_info:
        print("Could not retrieve order info")
        return
    
    numerator = int(trim_match.group(1))
    denominator = int(trim_match.group(2))
    trim_percentage = numerator / denominator
    
    print(f"Trim message: {numerator}/{denominator} = {trim_percentage:.2%}")
    
    original_action = order_info["order_info"]["action"]
    original_quantities = order_info["order_info"]["quantities"]
    
    is_buy = original_action == "buy"
    close_is_buy = not is_buy
    
    personal_close_qty = int(original_quantities["personal"] * trim_percentage)
    webhook_close_qty = int(original_quantities["webhook"] * trim_percentage)
    
    print(f"Closing quantities: Personal={personal_close_qty}, Webhook={webhook_close_qty}")
    
    try:
        if personal_close_qty >= 1:
            print(f"Would submit personal close order: qty={personal_close_qty}, is_buy={close_is_buy}")
        else:
            print(f"Skipping personal close order - quantity is {personal_close_qty} (must be >= 1)")
        
        if webhook_close_qty >= 1:
            webhook_payload = {
                "ticker": config.TICKER_SYMBOL,
                "price": "",
                "action": "sell",
                "orderType": "market"
            }
            
            order_executor.send_webhook(webhook_payload, config.WEBHOOK_URL, webhook_close_qty, "Close webhook")
        else:
            print(f"Skipping webhook submission - quantity is {webhook_close_qty} (must be >= 1)")
        
        if trim_percentage >= 1.0:
            position_tracker.clear_open_order()
            print("Order fully closed and cleared")
        else:
            remaining_quantities = {
                "personal": original_quantities["personal"] - personal_close_qty,
                "webhook": original_quantities["webhook"] - webhook_close_qty
            }
            
            order_info["order_info"]["quantities"] = remaining_quantities
            position_tracker.save_open_order(order_info["order_info"])
            print(f"Order updated with remaining quantities: {remaining_quantities}")
            
            if numerator == 1 and denominator == 8:
                entry_price = order_info["order_info"].get("price")
                remaining_webhook_qty = remaining_quantities.get("webhook", 0)
                if entry_price is None:
                    print("Cannot place stop after 1/8 trim - original entry price not available")
                elif remaining_webhook_qty < 1:
                    print(f"Skipping stop order submission after 1/8 trim - quantity is {remaining_webhook_qty} (must be >= 1)")
                else:
                    stop_price = float(entry_price) - 3.0
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                    stop_webhook_payload = {
                        "ticker": config.TICKER_SYMBOL,
                        "action": "sell",
                        "time": current_time,
                        "orderType": "stop",
                        "stopPrice": str(stop_price),
                        "quantityType": "fixed_quantity"
                    }
                    order_executor.send_webhook(stop_webhook_payload, config.WEBHOOK_URL, remaining_webhook_qty, "1/8 trim stop order webhook")
                    print(f"Stop order placed after 1/8 trim at {stop_price} (3 points below entry {entry_price}) for {remaining_webhook_qty} contract(s)")
            
    except Exception as e:
        print(f"Error submitting close orders: {e}")

def handle_stopped_message():
    print("Stopped message received - calling flat and cancel methods")
    
    try:
        print("Would call flatten_and_cancel methods")
        
        if position_tracker.has_open_order():
            position_tracker.clear_open_order()
            print("Open order cleared")
        
        webhook_payload = {
            "ticker": config.TICKER_SYMBOL,
            "action": "exit",
            "orderType": "market",
        }
        
        order_executor.send_webhook(webhook_payload, config.WEBHOOK_URL, config.GLOBAL_QUANTITY, "Stopped webhook")
        
        print("Stopped message handling completed")
        
    except Exception as e:
        print(f"Error handling stopped message: {e}")

def handle_long_triggered_message(triggered_match, source="second_channel"):
    if position_tracker.has_open_order():
        print("Order already open, skipping new order submission")
        return
    
    print(f"Long Triggered message received from {source}")
    
    ticker = config.TICKER_SYMBOL
    interval = int(triggered_match.group(2))
    level = float(triggered_match.group(3))
    score = triggered_match.group(4)
    price = float(triggered_match.group(5))
    time_str = triggered_match.group(6)
    
    print(f"Parsed values: Ticker={ticker}, Interval={interval}, Level={level}, Score={score}, Price={price}, Time={time_str}")
    
    is_buy = True
    order_type = 1
    
    score_parts = score.split('/')
    if len(score_parts) == 2:
        score_value = int(score_parts[0])
        score_max = int(score_parts[1])
        
        if source == "second_channel":
            if score_value < 5:
                print(f"Score {score_value} is below minimum threshold of 5 for second channel, skipping trade")
                return
        else:
            if score_value < 5:
                print(f"Score {score_value} is not greater than 5 for FBD endpoint, skipping trade")
                return
        
        personal_qty = min(15, max(5, score_value * 2))
    else:
        print(f"Invalid score format: {score}, skipping trade")
        return
    
    try:
        result1 = "SIMULATED_ORDER_RESULT"
        print(f"Would submit personal order: qty={personal_qty}, is_buy={is_buy}, order_type={order_type}")
        webhook_qty = config.GLOBAL_QUANTITY
        order_info = {
            "action": "buy",
            "direction": "long",
            "ticker": ticker,
            "interval": interval,
            "level": level,
            "score": score,
            "price": price,
            "time": time_str,
            "order_type": order_type,
            "source": source,
            "quantities": {
                "personal": personal_qty,
                "webhook": webhook_qty
            },
            "results": [
                str(result1) if result1 else None
            ]
        }
        position_tracker.save_open_order(order_info)
        print("Order saved locally")
        
        
        if webhook_qty > 0:
            webhook_payload = {
                "ticker": ticker,
                "price": str(price),
                "action": "buy",
                "orderType": "market"
            }
            
            additional_context = {
                "source": source,
                "direction": "long",
                "score": score,
                "level": level,
                "interval": interval
            }
            
            order_executor.send_webhook(webhook_payload, config.WEBHOOK_URL, webhook_qty, "Long Triggered webhook", is_entry_trade=True, additional_context=additional_context)
        else:
            print(f"Skipping webhook submission - quantity is {webhook_qty} (must be > 0)")
        
    except Exception as e:
        print(f"Error submitting Long Triggered order: {e}")

def handle_target_hit_message(target_match, source="fbd_endpoint"):
    if not position_tracker.has_open_order():
        print("No open order to close for target hit")
        return
    
    print("Target 1 Hit message received - closing position")
    
    ticker = config.TICKER_SYMBOL
    interval = int(target_match.group(2))
    level = float(target_match.group(3))
    target_price = float(target_match.group(4))
    entry_price = float(target_match.group(5))
    profit = float(target_match.group(6))
    time_str = target_match.group(7)
    
    print(f"Parsed target hit values: Ticker={ticker}, Interval={interval}, Level={level}, Target={target_price}, Entry={entry_price}, Profit={profit}, Time={time_str}")

    message_id = message_parser.create_message_id(ticker, target_price, entry_price, profit, time_str)
    
    if message_parser.is_message_processed(message_id):
        return
    
    try:
        order_info = position_tracker.get_open_order_info()
        if not order_info:
            print("Could not retrieve order info for target hit")
            return
        
        order_source = order_info["order_info"].get("source", "unknown")
        if order_source != source:
            print(f"Target 1 hit message ignored - order source is '{order_source}', only processing {source} orders")
            return
        
        original_action = order_info["order_info"]["action"]
        original_quantities = order_info["order_info"]["quantities"]
        
        is_buy = original_action == "buy"
        close_is_buy = not is_buy
        
        webhook_total_qty = original_quantities.get("webhook", 0)
        webhook_close_qty = int(webhook_total_qty / 2)
        remaining_webhook_qty = webhook_total_qty - webhook_close_qty
        
        print(f"Target 1 hit: Closing {webhook_close_qty} of {webhook_total_qty} webhook contracts, remaining: {remaining_webhook_qty}")
        
        if webhook_close_qty >= 1:
            webhook_payload = {
                "ticker": ticker,
                "price": str(target_price),
                "action": "sell",
                "orderType": "market"
            }
            
            order_executor.send_webhook(webhook_payload, config.WEBHOOK_URL, webhook_close_qty, "Target hit close webhook")
        else:
            print(f"Skipping webhook submission - quantity is {webhook_close_qty} (must be >= 1)")
        
        if remaining_webhook_qty >= 1:
            stop_price = entry_price - 3.0
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            
            stop_webhook_payload = {
                "ticker": ticker,
                "action": "sell",
                "time": current_time,
                "orderType": "stop",
                "stopPrice": str(stop_price),
                "quantityType": "fixed_quantity"
            }
            
            order_executor.send_webhook(stop_webhook_payload, config.WEBHOOK_URL, remaining_webhook_qty, "Target hit stop order webhook")
            print(f"Stop order placed at {stop_price} (3 points below entry {entry_price}) for {remaining_webhook_qty} contract(s)")
            
            remaining_quantities = {
                "personal": original_quantities.get("personal", 0),
                "webhook": remaining_webhook_qty
            }
            
            order_info["order_info"]["quantities"] = remaining_quantities
            position_tracker.save_open_order(order_info["order_info"])
            print(f"Order updated with remaining quantities: {remaining_quantities}")
        else:
            print(f"Skipping stop order submission - quantity is {remaining_webhook_qty} (must be >= 1)")
            position_tracker.clear_open_order()
            print("Position fully closed due to target hit")
        
        print(f"Target 1 hit processed. Profit: {profit} pts")
        
        message_parser.mark_message_processed(message_id)
        
    except Exception as e:
        print(f"Error handling target hit message: {e}")

def handle_target2_hit_message(target2_match, source="second_channel"):
    if not position_tracker.has_open_order():
        print("No open order to close for target 2 hit")
        return
    
    print("Target 2 Hit message received - closing remaining position")
    
    ticker = config.TICKER_SYMBOL
    interval = int(target2_match.group(2))
    level = float(target2_match.group(3))
    target_price = float(target2_match.group(4))
    entry_price = float(target2_match.group(5))
    profit = float(target2_match.group(6))
    time_str = target2_match.group(7)
    
    print(f"Parsed target 2 hit values: Ticker={ticker}, Interval={interval}, Level={level}, Target={target_price}, Entry={entry_price}, Profit={profit}, Time={time_str}")
    
    message_id = message_parser.create_message_id(ticker, target_price, entry_price, profit, time_str)
    
    if message_parser.is_message_processed(message_id):
        return
    
    try:
        order_info = position_tracker.get_open_order_info()
        if not order_info:
            print("Could not retrieve order info for target 2 hit")
            return
        
        order_source = order_info["order_info"].get("source", "unknown")
        if order_source != source:
            print(f"Target 2 hit message ignored - order source is '{order_source}', only processing {source} orders")
            return
        
        original_action = order_info["order_info"]["action"]
        original_quantities = order_info["order_info"]["quantities"]
        
        webhook_close_qty = original_quantities.get("webhook", 0)
        
        if webhook_close_qty > 0:
            webhook_payload = {
                "ticker": ticker,
                "price": str(target_price),
                "action": "exit",
                "orderType": "market"
            }
            
            order_executor.send_webhook(webhook_payload, config.WEBHOOK_URL, webhook_close_qty, "Target 2 close webhook")
        else:
            print(f"Skipping webhook submission - quantity is {webhook_close_qty} (must be > 0)")
        
        position_tracker.clear_open_order()
        print(f"Remaining position closed due to target 2 hit. Profit: {profit} pts")
        
        message_parser.mark_message_processed(message_id)
        
    except Exception as e:
        print(f"Error handling target 2 hit message: {e}")

def handle_stop_loss_message(stop_loss_match, source="fbd_endpoint"):
    if not position_tracker.has_open_order():
        print("No open order to close for stop loss hit")
        return
    
    print("Stop Loss Hit message received - closing position")
    
    ticker = config.TICKER_SYMBOL
    interval = int(stop_loss_match.group(2))
    level = float(stop_loss_match.group(3))
    entry_price = float(stop_loss_match.group(4))
    exit_price = float(stop_loss_match.group(5))
    loss = float(stop_loss_match.group(6))
    time_str = stop_loss_match.group(7)
    
    print(f"Parsed stop loss values: Ticker={ticker}, Interval={interval}, Level={level}, Entry={entry_price}, Exit={exit_price}, Loss={loss}, Time={time_str}")
    
    message_id = message_parser.create_message_id(ticker, exit_price, entry_price, loss, time_str)
    
    if message_parser.is_message_processed(message_id):
        print(f"Stop loss message already processed (ID: {message_id}), skipping duplicate")
        return
    
    try:
        order_info = position_tracker.get_open_order_info()
        if not order_info:
            print("Could not retrieve order info for stop loss hit")
            return
        
        order_source = order_info["order_info"].get("source", "unknown")
        if order_source != source:
            print(f"Stop loss message ignored - order source is '{order_source}', only processing {source} orders")
            return
        
        original_action = order_info["order_info"]["action"]
        original_quantities = order_info["order_info"]["quantities"]
        
        webhook_close_qty = original_quantities.get("webhook", 0)
        
        if webhook_close_qty > 0:
            webhook_payload = {
                "ticker": ticker,
                "price": str(exit_price),
                "action": "exit",
                "orderType": "market"
            }
            
            order_executor.send_webhook(webhook_payload, config.WEBHOOK_URL, webhook_close_qty, "Stop loss close webhook")
        else:
            print(f"Skipping webhook submission - quantity is {webhook_close_qty} (must be > 0)")
        
        position_tracker.clear_open_order()
        print(f"Position closed due to stop loss hit. Loss: {loss} pts")
        
        message_parser.mark_message_processed(message_id)
        
    except Exception as e:
        print(f"Error handling stop loss message: {e}")

def handle_stop_loss_simple_message(stop_loss_match, source="second_channel"):
    if not position_tracker.has_open_order():
        print("No open order to close for stop loss hit")
        return
    
    print("Stop Loss message received - closing position")
    
    ticker = config.TICKER_SYMBOL
    interval = int(stop_loss_match.group(2))
    level = float(stop_loss_match.group(3))
    entry_price = float(stop_loss_match.group(4))
    exit_price = float(stop_loss_match.group(5))
    loss = float(stop_loss_match.group(6))
    time_str = datetime.now().isoformat()
    
    print(f"Parsed stop loss values: Ticker={ticker}, Interval={interval}, Level={level}, Entry={entry_price}, Exit={exit_price}, Loss={loss}")
    
    message_id = message_parser.create_message_id(ticker, exit_price, entry_price, loss, time_str)
    
    if message_parser.is_message_processed(message_id):
        return
    
    try:
        order_info = position_tracker.get_open_order_info()
        if not order_info:
            print("Could not retrieve order info for stop loss hit")
            return
        
        order_source = order_info["order_info"].get("source", "unknown")
        if order_source != source:
            print(f"Stop loss message ignored - order source is '{order_source}', only processing {source} orders")
            return
        
        original_action = order_info["order_info"]["action"]
        original_quantities = order_info["order_info"]["quantities"]
        
        webhook_close_qty = original_quantities.get("webhook", 0)
        
        if webhook_close_qty > 0:
            webhook_payload = {
                "ticker": ticker,
                "price": str(exit_price),
                "action": "exit",
                "orderType": "market"
            }
            
            order_executor.send_webhook(webhook_payload, config.WEBHOOK_URL, webhook_close_qty, "Stop loss close webhook")
        else:
            print(f"Skipping webhook submission - quantity is {webhook_close_qty} (must be > 0)")
        
        position_tracker.clear_open_order()
        print(f"Position closed due to stop loss hit. Loss: {loss} pts")
        
        message_parser.mark_message_processed(message_id)
        
    except Exception as e:
        print(f"Error handling stop loss message: {e}")

def check_last_message():
    if not is_weekday():
        return
    
    try:
        position_tracker.reset_orders_if_expired()
        
        msg = discord_scraper.fetch_last_message()
        if not msg:
            print("No messages found.")
            return

        content = msg.get("content", "")
        mention_everyone = msg.get("mention_everyone", False)
        msg_id = msg.get("id")

        stopped_match = message_parser.parse_stopped_message(content)
        if mention_everyone and stopped_match:
            if msg_id and discord_scraper.is_discord_message_processed(msg_id):
                return
            
            handle_stopped_message()
            if msg_id:
                discord_scraper.mark_discord_message_processed(msg_id)
            return

        trim_match = message_parser.parse_trim_message(content)
        if mention_everyone and trim_match:
            msg_id = msg.get("id")
            if msg_id and discord_scraper.is_discord_message_processed(msg_id):
                print(f"Trim message already processed (Discord message ID: {msg_id}), skipping duplicate")
                return
            
            numerator = int(trim_match.group(1))
            denominator = int(trim_match.group(2))
            time_str = msg.get("timestamp", datetime.now().isoformat())
            message_id = message_parser.create_message_id("trim", numerator, denominator, 0, time_str)
            
            if message_parser.is_message_processed(message_id):
                if msg_id:
                    discord_scraper.mark_discord_message_processed(msg_id)
                return
            
            handle_trim_message(trim_match)
            if msg_id:
                discord_scraper.mark_discord_message_processed(msg_id)
            message_parser.mark_message_processed(message_id)
            return

        match = message_parser.parse_es_order_message(content)
        if mention_everyone and match:
            if position_tracker.has_open_order():
                print("Order already open, skipping new order submission")
                return
                
            print("Matched message:")
            print(content)
            
            order_direction = match.group(1).lower()
            long_value = match.group(2)
            letter = match.group(3).upper()
            stop_value = match.group(4)
            
            print(f"Retrieved values: ES {order_direction}: {long_value}, Letter: {letter}, Stop: {stop_value}")
            
            order_type = 1
            if order_direction == "long":
                is_buy = True
            else:
                is_buy = False
            
            if letter == 'A':
                personal_qty = config.GLOBAL_QUANTITY
                webhook_qty = config.GLOBAL_QUANTITY
            elif letter == 'B':
                personal_qty = config.GLOBAL_QUANTITY
                webhook_qty = 8
            elif letter == 'C':
                personal_qty = config.GLOBAL_QUANTITY
                webhook_qty = 5
            else:
                print(f"Ignoring order with letter '{letter}' - only 'A', 'B', 'C' orders are processed")
                return
            
            try:
                result1 = "SIMULATED_ORDER_RESULT"
                print(f"Would submit order from Discord message: is_buy={is_buy}, qty={personal_qty}, order_type={order_type}")
                print(result1)
                
                order_info = {
                    "action": "buy" if is_buy else "sell",
                    "direction": order_direction,
                    "ticker": config.TICKER_SYMBOL,
                    "letter": letter,
                    "stop_value": stop_value,
                    "order_type": order_type,
                    "source": "discord_message",
                    "quantities": {
                        "personal": personal_qty,
                        "webhook": webhook_qty
                    },
                    "results": [
                        str(result1) if result1 else None
                    ]
                }
                position_tracker.save_open_order(order_info)
                print("Order saved locally")
                
                if webhook_qty > 0:
                    webhook_payload = {
                        "ticker": config.TICKER_SYMBOL,
                        "price": str(long_value),
                        "action": "buy" if is_buy else "exit",
                        "orderType": "market",
                        "quantity": str(webhook_qty)
                    }
                    
                    additional_context = {
                        "source": "discord_message",
                        "direction": order_direction,
                        "letter": letter,
                        "stop_value": stop_value
                    }
                    
                    order_executor.send_webhook(webhook_payload, config.WEBHOOK_URL, webhook_qty, "Discord message webhook", is_entry_trade=is_buy, additional_context=additional_context)
                else:
                    print(f"Skipping webhook submission - quantity is {webhook_qty} (must be > 0)")
                
            except Exception as e:
                print(f"Error submitting order: {e}")
        else:
            if not discord_scraper.is_invalid_message_logged(msg_id, content):
                print(content)
                discord_scraper.mark_invalid_message_logged(msg_id, content)

    except Exception as e:
        print(f"Error: {e}")

def check_second_channel():
    if not is_weekday():
        return
    
    try:
        messages = discord_scraper.fetch_second_channel_messages()
       
        if not messages:
            print("No messages found in second channel")
            return

        msg = messages[0]
        msg_id = msg.get("id")
       
        embeds = msg.get("embeds", [])
       
        embed_content = ""
        
        if embeds and len(embeds) > 0:
            embed_content = embeds[0].get("description", "")
        
        stopped_match = message_parser.parse_stopped_message(embed_content)
        if stopped_match:
            if msg_id and discord_scraper.is_discord_message_processed(msg_id):
                return
            
            print("Stopped message found in second channel:")
            handle_stopped_message()
            if msg_id:
                discord_scraper.mark_discord_message_processed(msg_id)
            return
        
        target_hit_match = message_parser.parse_target_hit_message(embed_content)
        if target_hit_match:
            if msg_id and discord_scraper.is_discord_message_processed(msg_id):
                return
            
            ticker = config.TICKER_SYMBOL
            target_price = float(target_hit_match.group(4))
            entry_price = float(target_hit_match.group(5))
            profit = float(target_hit_match.group(6))
            time_str = target_hit_match.group(7)
            message_id = message_parser.create_message_id(ticker, target_price, entry_price, profit, time_str)
            
            if message_parser.is_message_processed(message_id):
                if msg_id:
                    discord_scraper.mark_discord_message_processed(msg_id)
                return
            
            print("Target 1 Hit message found in second channel:")
            handle_target_hit_message(target_hit_match, source="second_channel")
            if msg_id:
                discord_scraper.mark_discord_message_processed(msg_id)
            return
        
        target2_hit_match = message_parser.parse_target2_hit_message(embed_content)
        if target2_hit_match:
            if msg_id and discord_scraper.is_discord_message_processed(msg_id):
                return
            
            ticker = config.TICKER_SYMBOL
            target_price = float(target2_hit_match.group(4))
            entry_price = float(target2_hit_match.group(5))
            profit = float(target2_hit_match.group(6))
            time_str = target2_hit_match.group(7)
            message_id = message_parser.create_message_id(ticker, target_price, entry_price, profit, time_str)
            
            if message_parser.is_message_processed(message_id):
                if msg_id:
                    discord_scraper.mark_discord_message_processed(msg_id)
                return
            
            print("Target 2 Hit message found in second channel:")
            handle_target2_hit_message(target2_hit_match, source="second_channel")
            if msg_id:
                discord_scraper.mark_discord_message_processed(msg_id)
            return
        
        stop_loss_match = message_parser.parse_stop_loss_message(embed_content)
        if stop_loss_match:
            if msg_id and discord_scraper.is_discord_message_processed(msg_id):
                print(f"Stop Loss Hit message already processed (Discord message ID: {msg_id}), skipping duplicate")
                return
            
            ticker = config.TICKER_SYMBOL
            entry_price = float(stop_loss_match.group(4))
            exit_price = float(stop_loss_match.group(5))
            loss = float(stop_loss_match.group(6))
            time_str = stop_loss_match.group(7)
            message_id = message_parser.create_message_id(ticker, exit_price, entry_price, loss, time_str)
            
            if message_parser.is_message_processed(message_id):
                if msg_id:
                    discord_scraper.mark_discord_message_processed(msg_id)
                return
            
            print("Stop Loss Hit message found in second channel:")
            handle_stop_loss_message(stop_loss_match, source="second_channel")
            if msg_id:
                discord_scraper.mark_discord_message_processed(msg_id)
            return
        
        stop_loss_simple_match = message_parser.parse_stop_loss_simple_message(embed_content)
        if stop_loss_simple_match and "Loss:" in embed_content:
            if msg_id and discord_scraper.is_discord_message_processed(msg_id):
                return
            
            ticker = config.TICKER_SYMBOL
            entry_price = float(stop_loss_simple_match.group(4))
            exit_price = float(stop_loss_simple_match.group(5))
            loss = float(stop_loss_simple_match.group(6))
            time_str = datetime.now().isoformat()
            message_id = message_parser.create_message_id(ticker, exit_price, entry_price, loss, time_str)
            
            if message_parser.is_message_processed(message_id):
                if msg_id:
                    discord_scraper.mark_discord_message_processed(msg_id)
                return
            
            print("Stop Loss message found in second channel (simple format):")
            handle_stop_loss_simple_message(stop_loss_simple_match, source="second_channel")
            if msg_id:
                discord_scraper.mark_discord_message_processed(msg_id)
            return
        
        triggered_match = message_parser.parse_long_triggered_message(embed_content)
        if triggered_match:
            if msg_id and discord_scraper.is_discord_message_processed(msg_id):
                print(f"Long Triggered message already processed (Discord message ID: {msg_id}), skipping duplicate")
                return
            
            ticker = config.TICKER_SYMBOL
            interval = int(triggered_match.group(2))
            level = float(triggered_match.group(3))
            score = triggered_match.group(4)
            price = float(triggered_match.group(5))
            time_str = triggered_match.group(6)
            message_id = message_parser.create_message_id(ticker, price, price, 0, time_str)
            
            if message_parser.is_message_processed(message_id):
                print(f"Long Triggered message already processed (content ID: {message_id}), skipping duplicate")
                if msg_id:
                    discord_scraper.mark_discord_message_processed(msg_id)
                return
            
            print("Long Triggered message found in second channel: " + datetime.now().isoformat())
            handle_long_triggered_message(triggered_match, source="second_channel")
            if msg_id:
                discord_scraper.mark_discord_message_processed(msg_id)
            return

    except Exception as e:
        print(f"Error checking second channel: {e}")

if __name__ == "__main__":
    while True:
        check_last_message()
        # check_second_channel()
        time.sleep(1)
