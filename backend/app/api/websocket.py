import asyncio
import json
import yfinance as yf
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

async def send_stock_data(websocket: WebSocket, symbol: str):
    ticker = yf.Ticker(symbol)
    while True:
        try:
            # Fetch live data safely
            try:
                price = ticker.fast_info['last_price']
                prev = ticker.fast_info['previous_close']
                change = ((price - prev) / prev) * 100
            except:
                price = 0.0
                change = 0.0

            data = {
                "symbol": symbol.upper(),
                "price": round(price, 2),
                "change": round(change, 2),
                "timestamp": "Live"
            }
            await websocket.send_text(json.dumps(data))
            await asyncio.sleep(3) # 3s delay to avoid bans
        except Exception:
            break

@router.websocket("/ws/stocks/{symbol}")
async def websocket_endpoint_symbol(websocket: WebSocket, symbol: str):
    await websocket.accept()
    try:
        await send_stock_data(websocket, symbol)
    except Exception as e:
        print(f"Error: {e}")
        try: await websocket.close()
        except: pass

@router.websocket("/ws/stocks")
async def websocket_endpoint_default(websocket: WebSocket):
    await websocket.accept()
    try:
        # Default to AAPL if no symbol provided
        await send_stock_data(websocket, "AAPL")
    except Exception as e:
        print(f"Error: {e}")
        try: await websocket.close()
        except: pass