import asyncio
import telegram
import os
from dotenv import load_dotenv
from datetime import datetime, time, timedelta, timezone
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
import uvicorn

load_dotenv()
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')
PORT = int(os.getenv('PORT', 8000))

# 전역 변수로 설정 저장
settings = {
    "target_time": "23:20",
    "is_active": True,
    "message": "미장 알람"
}

app = FastAPI()
templates = Jinja2Templates(directory="templates")

async def send_daily_message():
    token = BOT_TOKEN
    chat_id = CHANNEL_ID
    bot = telegram.Bot(token=token)

    message = settings["message"]
    await bot.send_message(chat_id, message)

async def get_next_run_time(target_time):
    # 한국 시간대 설정 (UTC+9)
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    
    # 오늘 날짜에 설정된 시간을 결합
    next_run = datetime.combine(now.date(), target_time)
    next_run = next_run.replace(tzinfo=kst)
    
    # 현재 시간이 설정된 시간보다 늦으면 다음날로 설정
    if now > next_run:
        next_run += timedelta(days=1)
    
    return next_run

async def run_bot():
    while True:
        if not settings["is_active"]:
            await asyncio.sleep(60)
            continue

        target_time = datetime.strptime(settings["target_time"], "%H:%M").time()
        next_run = await get_next_run_time(target_time)
        kst = timezone(timedelta(hours=9))
        now = datetime.now(kst)
        
        wait_seconds = (next_run - now).total_seconds()
        if wait_seconds > 0:
            await asyncio.sleep(wait_seconds)
        
        await send_daily_message()

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(run_bot())

# 웹 라우트
@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "settings": settings}
    )

@app.post("/settings")
async def update_settings(
    target_time: str = Form(...),
    is_active: bool = Form(False),
    message: str = Form(...)
):
    settings["target_time"] = target_time
    settings["is_active"] = is_active
    settings["message"] = message
    return RedirectResponse(url="/", status_code=303)

@app.post("/send_now")
async def send_now():
    await send_daily_message()
    return RedirectResponse(url="/", status_code=303)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)