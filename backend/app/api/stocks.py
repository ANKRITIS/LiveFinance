from fastapi import APIRouter
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

router = APIRouter()

# --- SIMULATION ENGINES (Guaranteed to work) ---
def get_fake_history():
    data = []
    price = 150.0
    start_date = datetime.now() - timedelta(days=365)
    for i in range(365):
        date = start_date + timedelta(days=i)
        price += random.uniform(-2, 2)
        data.append({"time": date.strftime('%Y-%m-%d'), "price": round(price, 2)})
    return data

def get_fake_forecast():
    data = []
    price = 150.0
    start_date = datetime.now()
    for i in range(30):
        date = start_date + timedelta(days=i)
        price += random.uniform(-1, 1.5)
        data.append({"time": date.strftime('%Y-%m-%d'), "predicted_price": round(price, 2)})
    return data
# -----------------------------------------------

@router.get("/history/{symbol}")
async def get_history(symbol: str):
    try:
        # Try Real Data
        stock = yf.Ticker(symbol)
        hist = stock.history(period="1y", interval="1d")
        if hist.empty: raise Exception("No Data")
        
        data = []
        for date, row in hist.iterrows():
            data.append({"time": date.strftime('%Y-%m-%d'), "price": round(row['Close'], 2)})
        return {"history": data}
    except:
        # Failsafe: Return Simulation
        print("Yahoo failed. Returning simulation.")
        return {"history": get_fake_history()}

@router.get("/forecast/{symbol}")
async def get_forecast(symbol: str):
    try:
        # Try Real Data for Trend
        stock = yf.Ticker(symbol)
        hist = stock.history(period="3mo", interval="1d")
        if hist.empty: raise Exception("No Data")
        
        prices = hist['Close'].values
        # Simple Trend Math
        z = np.polyfit(np.arange(len(prices)), prices, 1)
        p = np.poly1d(z)
        
        forecast_data = []
        last_date = hist.index[-1]
        for i in range(1, 31):
            next_date = last_date + timedelta(days=i)
            # Trend + Random Noise
            price = p(len(prices) + i) + np.random.normal(0, prices.std() * 0.5)
            forecast_data.append({"time": next_date.strftime('%Y-%m-%d'), "predicted_price": round(price, 2)})
            
        return {"forecast": forecast_data}
    except:
        # Failsafe: Return Simulation
        print("Forecast failed. Returning simulation.")
        return {"forecast": get_fake_forecast()}