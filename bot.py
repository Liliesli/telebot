import asyncio
import telegram
import os
import json
import threading
import requests
import time
import csv
from io import StringIO
from dotenv import load_dotenv
from datetime import datetime, time, timedelta, timezone
from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
import uvicorn
from typing import List

load_dotenv()
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')
PORT = int(os.getenv('PORT', 8000))
SERVER_URL = os.getenv('SERVER_URL', 'https://telebot-1frg.onrender.com')  # 서버 URL 환경변수 추가

# 한국 시간대 고정 (UTC+9)
kst = timezone(timedelta(hours=9))
# 미국 시간대 추가 (UTC-4, EDT)
edt = timezone(timedelta(hours=-4))

def get_korea_time():
    return datetime.now(kst)

def get_us_time():
    return datetime.now(edt)

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
    },
    "holidays": []  # 알람을 보내지 않을 날짜들 (형식: "YYYY-MM-DD")
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
    now = get_us_time()
    print(f"현재 미국 시간: {now}")
    
    # 오늘 날짜에 설정된 시간을 결합 (미국 시간 기준)
    next_run = datetime.combine(now.date(), target_time)
    next_run = next_run.replace(tzinfo=edt)
    print(f"다음 실행 시간 (미국): {next_run}")
    print(f"다음 실행 시간 (한국): {next_run.astimezone(kst)}")
    
    # 현재 시간이 설정된 시간보다 늦으면 다음날로 설정
    if now > next_run:
        next_run += timedelta(days=1)
        print(f"다음날로 설정됨 (미국): {next_run}")
        print(f"다음날로 설정됨 (한국): {next_run.astimezone(kst)}")
    
    return next_run

def is_holiday(date):
    """주어진 날짜가 휴일인지 확인"""
    date_str = date.strftime("%Y-%m-%d")
    return date_str in settings["holidays"]

async def run_bot():
    print("봇 시작됨")
    while True:
        for alarm_type in ["open", "close"]:
            alarm_settings = settings["alarms"][alarm_type]
            
            if not alarm_settings["is_active"] or not alarm_settings["target_time"]:
                print(f"{alarm_type} 알람이 비활성화되어 있거나 시간이 설정되지 않음")
                continue

            us_now = get_us_time()
            
            # 주말(토요일=5, 일요일=6) 체크 - 미국 시간 기준
            if us_now.weekday() >= 5:
                print(f"미국 시간 기준 주말이므로 {alarm_type} 알람을 보내지 않습니다.")
                continue
                
            # 휴일 체크
            if is_holiday(us_now.date()):
                print(f"휴일이므로 {alarm_type} 알람을 보내지 않습니다.")
                continue

            # 설정된 시간을 파싱
            target_time = datetime.strptime(alarm_settings["target_time"], "%H:%M").time()
            print(f"현재 설정된 {alarm_type} 시간 (미국): {alarm_settings['target_time']}")
            
            next_run = await get_next_run_time(target_time)
            now = get_us_time()
            
            wait_seconds = (next_run - now).total_seconds()
            print(f"{alarm_type} 대기 시간: {wait_seconds}초")
            
            if wait_seconds > 0 and wait_seconds <= 60:  # 1분 이내로 실행되어야 할 때
                await asyncio.sleep(wait_seconds)
                # 대기 후 다시 한번 주말과 휴일 체크
                us_now = get_us_time()
                if us_now.weekday() >= 5:
                    print(f"미국 시간 기준 주말이므로 {alarm_type} 알람을 보내지 않습니다.")
                    continue
                if is_holiday(us_now.date()):
                    print(f"휴일이므로 {alarm_type} 알람을 보내지 않습니다.")
                    continue
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

def convert_time_to_kst(time_str):
    """미국 시간을 한국 시간으로 변환"""
    if not time_str:
        return ""
    # 오늘 날짜의 미국 시간을 기준으로 datetime 객체 생성
    us_time = datetime.combine(get_us_time().date(), 
                             datetime.strptime(time_str, "%H:%M").time())
    us_time = us_time.replace(tzinfo=edt)
    # 한국 시간으로 변환
    kr_time = us_time.astimezone(kst)
    return kr_time.strftime("%H:%M")

@app.get("/")
async def root(request: Request):
    # 현재 설정된 시간들의 한국 시간 변환값 계산
    open_kr_time = convert_time_to_kst(settings["alarms"]["open"]["target_time"])
    close_kr_time = convert_time_to_kst(settings["alarms"]["close"]["target_time"])
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request, 
            "settings": settings,
            "open_kr_time": open_kr_time,
            "close_kr_time": close_kr_time
        }
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

@app.post("/upload-holidays")
async def upload_holidays(file: UploadFile = File(...)):
    try:
        # 파일 확장자 체크
        if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
            return {"error": "CSV 또는 Excel 파일만 업로드 가능합니다."}

        holidays = []
        content = await file.read()
        
        # CSV 파일 처리
        if file.filename.endswith('.csv'):
            text = content.decode('utf-8')
            csv_reader = csv.DictReader(StringIO(text))
            for row in csv_reader:
                try:
                    # date 컬럼에서 날짜 읽기
                    date_str = row['date'].strip()
                    # 날짜 형식 검증
                    datetime.strptime(date_str, "%Y-%m-%d")
                    holidays.append(date_str)
                except (ValueError, KeyError):
                    continue
        else:
            return {"error": "현재는 CSV 파일만 지원합니다. 엑셀 파일은 CSV로 변환 후 업로드해주세요."}
        
        if not holidays:
            return {"error": "유효한 날짜를 찾을 수 없습니다."}
        
        # 설정 업데이트
        settings['holidays'] = sorted(list(set(holidays)))  # 중복 제거 및 정렬
        save_settings(settings)
        
        return {"message": f"{len(holidays)}개의 휴일이 업로드되었습니다."}
    except Exception as e:
        return {"error": f"파일 업로드 중 오류 발생: {str(e)}"}

@app.post("/add-holiday")
async def add_holiday(date: str = Form(...)):
    try:
        # 날짜 형식 검증
        datetime.strptime(date, "%Y-%m-%d")
        if date not in settings['holidays']:
            settings['holidays'].append(date)
            settings['holidays'].sort()
            save_settings(settings)
        return RedirectResponse(url="/", status_code=303)
    except ValueError:
        return {"error": "잘못된 날짜 형식입니다. YYYY-MM-DD 형식으로 입력해주세요."}

@app.post("/remove-holiday")
async def remove_holiday(date: str = Form(...)):
    if date in settings['holidays']:
        settings['holidays'].remove(date)
        save_settings(settings)
    return RedirectResponse(url="/", status_code=303)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)