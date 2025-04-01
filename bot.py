import asyncio
import telegram
import os
import json
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

# 한국 시간대 고정 (UTC+9)
kst = timezone(timedelta(hours=9))

def get_korea_time():
    return datetime.now(kst)

# 설정 파일 경로
SETTINGS_FILE = "settings.json"

# 기본 설정
DEFAULT_SETTINGS = {
    "target_time": "22:30",
    "is_active": True,
    "message": "미장 알람"
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

async def send_daily_message():
    token = BOT_TOKEN
    chat_id = CHANNEL_ID
    bot = telegram.Bot(token=token)

    message = settings["message"]
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
        if not settings["is_active"]:
            print("알람이 비활성화되어 있음")
            await asyncio.sleep(60)
            continue

        # 설정된 시간을 파싱
        target_time = datetime.strptime(settings["target_time"], "%H:%M").time()
        print(f"현재 설정된 시간: {settings['target_time']}")
        
        next_run = await get_next_run_time(target_time)
        now = get_korea_time()
        
        wait_seconds = (next_run - now).total_seconds()
        print(f"대기 시간: {wait_seconds}초")
        
        if wait_seconds > 0:
            await asyncio.sleep(wait_seconds)
        
        await send_daily_message()

async def restart_bot():
    global bot_task
    if bot_task:
        bot_task.cancel()
    bot_task = asyncio.create_task(run_bot())
    print("봇 재시작됨")

@app.on_event("startup")
async def startup_event():
    print("서버 시작됨")
    # 시작 시 현재 시간 확인
    now = get_korea_time()
    print(f"서버 시작 시간: {now}")
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
    target_time: str = Form(...),
    is_active: bool = Form(False),
    message: str = Form(...)
):
    print(f"설정 업데이트: 시간={target_time}, 활성화={is_active}, 메시지={message}")
    settings["target_time"] = target_time
    settings["is_active"] = is_active
    settings["message"] = message
    save_settings(settings)  # 설정을 파일에 저장
    await restart_bot()  # 봇 재시작
    return RedirectResponse(url="/", status_code=303)

@app.post("/send_now")
async def send_now():
    print("수동 메시지 전송 요청")
    await send_daily_message()
    return RedirectResponse(url="/", status_code=303)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)