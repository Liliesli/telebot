import asyncio
import telegram
import os
from dotenv import load_dotenv
from datetime import datetime, time, timedelta
from fastapi import FastAPI
import uvicorn

load_dotenv()
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')
PORT = int(os.getenv('PORT', 8000))

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Bot is running"}

async def send_daily_message():
    token = BOT_TOKEN
    chat_id = CHANNEL_ID
    bot = telegram.Bot(token=token)

    message = "미장 알람"
    await bot.send_message(chat_id, message)

async def get_next_run_time(target_time):
    now = datetime.now()
    next_run = datetime.combine(now.date(), target_time)
    
    if now.time() > target_time:
        next_run += timedelta(days=1)
    
    return next_run

async def run_bot():
    target_time = time(23, 10)
    
    while True:
        next_run = await get_next_run_time(target_time)
        now = datetime.now()
        
        wait_seconds = (next_run - now).total_seconds()
        if wait_seconds > 0:
            await asyncio.sleep(wait_seconds)
        
        await send_daily_message()

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(run_bot())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)