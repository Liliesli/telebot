import asyncio
import telegram
import os
import json
import threading
import requests
import time
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
SERVER_URL = os.getenv('SERVER_URL', 'https://telebot-1frg.onrender.com')  # 서버 URL 환경변수 추가

# 한국 시간대 고정 (UTC+9)
kst = timezone(timedelta(hours=9))

def get_korea_time():
    return datetime.now(kst)

# 설정 파일 경로
SETTINGS_FILE = "settings.json"

# 기본 설정
DEFAULT_SETTINGS = {
    "alarms": {
        "open": {
            "target_time": "",
            "is_active": True,
            "message": "미장 오픈"
        },
        "close": {
            "target_time": "",
            "is_active": True,
            "message": "미장 닫음"
        }
    }
}

def load_settings():
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"설정 파일 로드 중 오류 발생: {e}")
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"설정 파일 저장 중 오류 발생: {e}")

# 전역 변수로 설정 저장
settings = load_settings()

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# 봇 태스크를 저장할 변수
bot_task = None

async def send_daily_message(alarm_type):
    token = BOT_TOKEN
    chat_id = CHANNEL_ID
    bot = telegram.Bot(token=token)

    message = settings["alarms"][alarm_type]["message"]
    await bot.send_message(chat_id, message)
    print(f"메시지 전송 완료: {message}")

async def get_next_run_time(target_time):
    now = get_korea_time()
    print(f"현재 시간: {now}")
    
    # 오늘 날짜에 설정된 시간을 결합
    next_run = datetime.combine(now.date(), target_time)
    next_run = next_run.replace(tzinfo=kst)
    print(f"다음 실행 시간: {next_run}")
    
    # 현재 시간이 설정된 시간보다 늦으면 다음날로 설정
    if now > next_run:
        next_run += timedelta(days=1)
        print(f"다음날로 설정됨: {next_run}")
    
    return next_run

async def run_bot():
    print("봇 시작됨")
    while True:
        for alarm_type in ["open", "close"]:
            alarm_settings = settings["alarms"][alarm_type]
            
            if not alarm_settings["is_active"] or not alarm_settings["target_time"]:
                print(f"{alarm_type} 알람이 비활성화되어 있거나 시간이 설정되지 않음")
                continue

            # 설정된 시간을 파싱
            target_time = datetime.strptime(alarm_settings["target_time"], "%H:%M").time()
            print(f"현재 설정된 {alarm_type} 시간: {alarm_settings['target_time']}")
            
            next_run = await get_next_run_time(target_time)
            now = get_korea_time()
            
            wait_seconds = (next_run - now).total_seconds()
            print(f"{alarm_type} 대기 시간: {wait_seconds}초")
            
            if wait_seconds > 0 and wait_seconds <= 60:  # 1분 이내로 실행되어야 할 때
                await asyncio.sleep(wait_seconds)
                await send_daily_message(alarm_type)

        await asyncio.sleep(30)  # 30초마다 체크

async def restart_bot():
    global bot_task
    if bot_task:
        bot_task.cancel()
    bot_task = asyncio.create_task(run_bot())
    print("봇 재시작됨")

# 주기적으로 서버에 ping을 보내는 함수
def ping_server():
    while True:
        try:
            requests.get(SERVER_URL)
            print("서버에 ping 전송")
        except Exception as e:
            print(f"ping 전송 중 오류 발생: {e}")
        time.sleep(600)  # 10분마다 ping 전송

@app.on_event("startup")
async def startup_event():
    print("서버 시작됨")
    # 시작 시 현재 시간 확인
    now = get_korea_time()
    print(f"서버 시작 시간: {now}")
    # ping 스레드 시작
    threading.Thread(target=ping_server, daemon=True).start()
    await restart_bot()

# 웹 라우트
@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "settings": settings}
    )

@app.post("/settings")
async def update_settings(
    open_time: str = Form(...),
    open_active: bool = Form(False),
    open_message: str = Form(...),
    close_time: str = Form(...),
    close_active: bool = Form(False),
    close_message: str = Form(...)
):
    print(f"설정 업데이트: 오픈={open_time}, 마감={close_time}")
    
    settings["alarms"]["open"].update({
        "target_time": open_time,
        "is_active": open_active,
        "message": open_message
    })
    
    settings["alarms"]["close"].update({
        "target_time": close_time,
        "is_active": close_active,
        "message": close_message
    })
    
    save_settings(settings)  # 설정을 파일에 저장
    await restart_bot()  # 봇 재시작
    return RedirectResponse(url="/", status_code=303)

@app.post("/send_now/{alarm_type}")
async def send_now(alarm_type: str):
    if alarm_type not in ["open", "close"]:
        return {"error": "Invalid alarm type"}
    print(f"수동 메시지 전송 요청: {alarm_type}")
    await send_daily_message(alarm_type)
    return RedirectResponse(url="/", status_code=303)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)