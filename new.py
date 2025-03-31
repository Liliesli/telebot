import asyncio
import telegram
import os
from dotenv import load_dotenv
from datetime import datetime, time, timedelta
import platform
import caffeinate  # macOS에서 절전 방지를 위한 라이브러리

load_dotenv()
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHANNEL_ID = int(os.getenv('TELEGRAM_CHANNEL_ID'))

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

async def main():
    # macOS에서 절전 모드 방지
    if platform.system() == 'Darwin':
        caffeinate_process = caffeinate.Caffeinate()
    
    target_time = time(23, 04)
    
    try:
        while True:
            next_run = await get_next_run_time(target_time)
            now = datetime.now()
            
            wait_seconds = (next_run - now).total_seconds()
            if wait_seconds > 0:
                await asyncio.sleep(wait_seconds)
            
            await send_daily_message()
    finally:
        # 프로그램 종료 시 절전 방지 해제
        if platform.system() == 'Darwin':
            caffeinate_process.stop()

if __name__ == "__main__":
    asyncio.run(main())