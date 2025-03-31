# https://velog.io/@kxxmz312/Telegram-bot-%EB%B4%87-%EB%A7%8C%EB%93%A4%EA%B8%B0-with-%ED%8C%8C%EC%9D%B4%EC%8D%AC
# nohup python3 new.py > nohup.out 2>&1 & # 백그라운드 실행
# tail -f nohup.out # 로그 확인
# pkill -f "python3 new.py" # 프로세스 종료
import asyncio
import telegram
import os
from dotenv import load_dotenv
from datetime import datetime, time, timedelta

load_dotenv()
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHANNEL_ID = int(os.getenv('TELEGRAM_CHANNEL_ID'))  # 문자열을 정수로 변환

async def send_daily_message():
    token = BOT_TOKEN
    chat_id = CHANNEL_ID
    bot = telegram.Bot(token=token)

    message = "미장 알람"
    await bot.send_message(chat_id, message)

async def get_next_run_time(target_time):
    now = datetime.now()
    next_run = datetime.combine(now.date(), target_time)
    
    # 만약 현재 시간이 목표 시간을 지났다면, 다음 날로 설정
    if now.time() > target_time:
        next_run += timedelta(days=1)
    
    return next_run

async def main():
    target_time = time(23, 04)  # 목표 시간: 10:25
    
    while True:
        next_run = await get_next_run_time(target_time)
        now = datetime.now()
        
        # 다음 실행 시간까지 대기
        wait_seconds = (next_run - now).total_seconds()
        if wait_seconds > 0:
            await asyncio.sleep(wait_seconds)
        
        # 메시지 전송
        await send_daily_message()

if __name__ == "__main__":
    asyncio.run(main())