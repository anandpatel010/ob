# Binance Spot Order Book Tape

A lightweight Python CLI tool to monitor real-time order book depth (best bid and ask) for Binance spot USDT pairs. Displays total volume at the current best prices with colored bars, updating every ~100ms for a clean, flicker-free experience.

## Overview

This script connects to Binance's public WebSocket API (`@depth@100ms`) to stream real-time order book data for any USDT trading pair (e.g., BTC/USDT). It shows the best ask (lowest sell) and best bid (highest buy) with their volumes in base asset and USD, formatted in a visually appealing ASCII table. Updates are displayed only when both ask and bid volumes exceed $100, ensuring a stable, paired output to prevent flickering. The display clears completely for each update, and proportional bars visualize volume size.

## Features

- **Real-time Order Book**: Streams depth updates via Binance WebSocket (`@depth@100ms`).
- **Best Ask/Bid Display**: Shows ask first, then bid, with volumes (base and USD), only when both exceed $100 to avoid flickering.
- **Dynamic Pair Switching**: Start with BTC/USDT; enter a symbol (e.g., `doge`) to switch to `[symbol]usdt`, validated via API.
- **Connection Status**: Cyan messages for successful connections; red for errors.
- **Robust Error Handling**: Skips invalid messages and retries connections without crashing, with detailed debug logging.
- **Clear Display**: Clears previous output for each ~100ms update for a clean CLI view.
- **Visuals**: Colored bars (cyan for BID, red for ASK, gold for $1M+ volumes) for depths >$10,000, one bar per $10k.
- **Pretty Formatting**: ASCII table with in-place updates every ~100ms for a smooth, non-scrolling display.
- **Output Format**: `[Time] | [Side] | [Price (USDT)] | [Volume (Base)] | [$Value] | [Depth bars]`.

## Requirements

- Python 3.7+
- `websockets` library (`pip install websockets`)
- `aiohttp` library (`pip install aiohttp`)

## Installation

1. Clone or download this repository:
   ```bash
   git clone (https://github.com/anandpatel010/ob.git)

<img width="1047" height="166" alt="image" src="https://github.com/user-attachments/assets/6c499542-55e8-4090-90ff-87600e7ed69a" />
