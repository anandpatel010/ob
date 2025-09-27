import asyncio
import websockets
import json
import time
import threading
import queue as thread_queue
import aiohttp  # For symbol validation

# ANSI colors
CYAN = "\033[36m"  # For bids and connection messages
RED = "\033[31m"   # For asks and errors
GOLD = "\033[33m"  # For $1M+ volumes
RESET = "\033[0m"

async def validate_symbol(symbol):
    """Check if a trading pair is valid on Binance."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.binance.com/api/v3/exchangeInfo?symbol={symbol.upper()}") as resp:
                data = await resp.json()
                return 'symbols' in data and any(s['symbol'] == symbol.upper() for s in data['symbols'])
    except Exception:
        return False

async def main():
    current_symbol = 'btcusdt'  # Start with BTC/USDT
    value_threshold = 100.0  # Show only depths with total $ value > this
    million_threshold = 1000000.0  # Use gold for volumes >= $1M
    bar_threshold = 10000  # USD per bar segment
    bar_char = "▬"

    # Thread for CLI input
    input_queue = thread_queue.Queue()  # Thread-safe queue
    def input_thread():
        while True:
            new_input = input().strip().lower()
            if new_input:
                new_symbol = new_input + 'usdt' if not new_input.endswith('usdt') else new_input
                input_queue.put(new_symbol)

    threading.Thread(target=input_thread, daemon=True).start()

    # Initial connection message
    upper_symbol = current_symbol.upper().replace('USDT', '/USDT')
    print(f"{CYAN}Connected to WebSocket for {upper_symbol}{RESET}")

    # Flag to track if table header has been printed
    header_printed = False

    while True:
        # Check for new symbol from input
        try:
            new_symbol = input_queue.get_nowait()
            if await validate_symbol(new_symbol):
                current_symbol = new_symbol
                upper_symbol = current_symbol.upper().replace('USDT', '/USDT')
                print(f"{CYAN}Connected to WebSocket for {upper_symbol}{RESET}")
                header_printed = False  # Reset header flag on symbol change
            else:
                print(f"{RED}Invalid symbol {new_symbol.upper()}. Keeping {upper_symbol}.{RESET}")
                continue
        except thread_queue.Empty:
            pass

        ws_url = f"wss://stream.binance.com:9443/ws/{current_symbol}@depth@100ms"
        if not header_printed:
            print(f"\nWatching order book depth for {upper_symbol} on Binance... (Enter new symbol like 'doge' to switch)")
            print(f"{'-'*50}")
            print(f"| {'Time':<12} | {'Side':<6} | {'Price (USDT)':<12} | {'Volume (Base)':<12} | {'$Value':<12} | {'Depth':<20} |")
            print(f"{'-'*50}")
            header_printed = True

        try:
            async with websockets.connect(ws_url) as ws:
                while True:
                    # Non-blocking check for new symbol
                    try:
                        new_symbol = input_queue.get_nowait()
                        if await validate_symbol(new_symbol):
                            current_symbol = new_symbol
                            upper_symbol = current_symbol.upper().replace('USDT', '/USDT')
                            print(f"{CYAN}Connected to WebSocket for {upper_symbol}{RESET}")
                            header_printed = False  # Reset header flag on symbol change
                            await ws.close()  # Close current WS to trigger reconnect with new symbol
                            break
                        else:
                            print(f"{RED}Invalid symbol {new_symbol.upper()}. Keeping {upper_symbol}.{RESET}")
                    except thread_queue.Empty:
                        pass

                    try:
                        message = await ws.recv()
                        data = json.loads(message)

                        # Validate message
                        if not isinstance(data, dict) or data.get('e') != 'depthUpdate' or 'E' not in data:
                            print(f"{RED}Invalid message received: {json.dumps(data)[:100]}. Skipping...{RESET}")
                            continue

                        ts = data['E']  # Use 'E' for event time in depthUpdate
                        seconds = ts / 1000
                        formatted_time = time.strftime('%H:%M:%S', time.localtime(seconds)) + f".{int((seconds % 1) * 1000):03d}"

                        # Get best bid and ask
                        bids = data.get('b', [])  # [[price, qty], ...]
                        asks = data.get('a', [])  # [[price, qty], ...]
                        if not bids or not asks:
                            #print(f"{RED}Empty bid/ask data in message: {json.dumps(data)[:100]}. Skipping...{RESET}")
                            continue

                        try:
                            best_bid = float(bids[0][0]) if bids else 0.0
                            best_ask = float(asks[0][0]) if asks else 0.0
                            bid_qty = float(bids[0][1]) if bids else 0.0
                            ask_qty = float(asks[0][1]) if asks else 0.0
                        except (IndexError, ValueError) as e:
                            print(f"{RED}Error parsing bid/ask data: {e}. Message: {json.dumps(data)[:100]}. Skipping...{RESET}")
                            continue

                        # Calculate notional values
                        bid_value = bid_qty * best_bid
                        ask_value = ask_qty * best_ask

                        # Only show if both ask and bid are above threshold
                        if bid_value > value_threshold and ask_value > value_threshold:
                            # Clear entire previous table (move to top and clear screen)
                            print("\033[H\033[J", end="")
                            # Redraw header
                            print(f"\nWatching order book depth for {upper_symbol} on Binance... (Enter new symbol like 'doge' to switch)")
                            print(f"{'-'*50}")
                            print(f"| {'Time':<12} | {'Side':<6} | {'Price (USDT)':<12} | {'Volume (Base)':<12} | {'$Value':<12} | {'Depth':<20} |")
                            print(f"{'-'*50}")

                            # Print ask first
                            color = GOLD if ask_value >= million_threshold else RED
                            num_bars = int(ask_value // bar_threshold)
                            bars = (color + bar_char + RESET) * num_bars
                            print(f"| {formatted_time:<12} | {color}ASK{RESET:<6} | {best_ask:<12.2f} | {ask_qty:<12.4f} | ${ask_value:<12,.0f} | {bars:<20} |")

                            # Print bid second
                            color = GOLD if bid_value >= million_threshold else CYAN
                            num_bars = int(bid_value // bar_threshold)
                            bars = (color + bar_char + RESET) * num_bars
                            print(f"| {formatted_time:<12} | {color}BID{RESET:<6} | {best_bid:<12.2f} | {bid_qty:<12.4f} | ${bid_value:<12,.0f} | {bars:<20} |")

                            print(f"{'-'*50}")

                    except (json.JSONDecodeError, KeyError, ValueError) as e:
                        print(f"{RED}Error parsing message for {upper_symbol}: {e}. Message: {json.dumps(data)[:100]}. Skipping...{RESET}")
                        continue

        except Exception as e:
            print(f"{RED}Connection Error for {upper_symbol}: {e}. Reconnecting in 1s...{RESET}")
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())