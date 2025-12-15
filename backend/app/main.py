from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import finnhub
import asyncio
import json
import boto3
import os
import pandas as pd
from datetime import datetime
from prophet import Prophet
import yfinance as yf


app = FastAPI()


# --- CONFIGURATION ---
FINNHUB_KEY = "d5o0711r01qma2b6ov1gd5o0711r01qma2b6ov20"
finnhub_client = finnhub.Client(api_key=FINNHUB_KEY)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- 1. AWS S3 (REAL CODE) ---
def archive_to_s3(ticker, data):
   #Keys needed
    aws_id = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret = os.getenv("AWS_SECRET_ACCESS_KEY")
   
    if not aws_id or not aws_secret:
        return


    try:
        s3 = boto3.client('s3', aws_access_key_id=aws_id, aws_secret_access_key=aws_secret)
        file_name = f"{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        s3.put_object(Bucket='livefinance-archive', Key=file_name, Body=json.dumps(data))
        print(f"✅ Uploaded {file_name} to S3")
    except Exception as e:
        print(f"AWS Upload Failed: {e}")


# --- 2. WEBSOCKET (LIVE DATA) ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)


manager = ConnectionManager()


@app.websocket("/ws/stock/{ticker}")
async def websocket_endpoint(websocket: WebSocket, ticker: str):
    await manager.connect(websocket)
    ticker = ticker.upper()
    try:
        while True:
            quote = finnhub_client.quote(ticker)
            if quote['c'] == 0:
                await websocket.send_json({"error": "Symbol not found"})
                break
           
            data = {
                "symbol": ticker,
                "price": quote['c'],
                "change": quote['dp'],
                "timestamp": datetime.now().strftime("%H:%M:%S")
            }
            await websocket.send_json(data)
            archive_to_s3(ticker, data)
            await asyncio.sleep(2)
    except Exception:
        manager.disconnect(websocket)


# --- 3. REAL TRENDING LIST (NEW) ---
@app.get("/api/trending")
def get_trending():
    # We check these popular stocks in real-time
    watch_list = ["NVDA", "TSLA", "AAPL", "AMZN", "MSFT", "AMD", "SPY", "COIN"]
    trending_data = []
   
    for symbol in watch_list:
        try:
            quote = finnhub_client.quote(symbol)
            trending_data.append({
                "symbol": symbol,
                "name": symbol, 
                "price": quote['c'],
                "change": quote['dp']
            })
        except:
            continue
           
    return trending_data


# --- 4. REAL HISTORY & AI ---
@app.get("/api/forecast/{ticker}")
def get_forecast(ticker: str):
    try:
        # REAL DATA from Yahoo Finance
        stock = yf.Ticker(ticker)
        history = stock.history(period="2y") 
       
        if history.empty:
            return {"error": "Ticker not found"}


        # Format for Prophet
        df = history.reset_index()[['Date', 'Close']]
        df.columns = ['ds', 'y']
        df['ds'] = df['ds'].dt.tz_localize(None)


        # AI Prediction
        m = Prophet()
        m.fit(df)
        future = m.make_future_dataframe(periods=30)
        forecast = m.predict(future)


        return {
            "forecast": forecast[['ds', 'yhat']].tail(30).to_dict('records'),
            "history": df.to_dict('records')
        }
    except Exception as e:
        return {"error": str(e)}
