import asyncio
import telegram
import os
import json
import threading
import requests
import time as time_module
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
import uvicorn
from typing import List
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import traceback


# 로깅 설정
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)



load_dotenv()
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')
PORT = int(os.getenv('PORT', 10000))
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
            "target_time": "09:00",
            "is_active": True,
            "message": "미장 오픈"
        },
        "close": {
            "target_time": "20:00",
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
                loaded_settings = json.load(f)
                # 기존 설정과 기본 설정을 병합
                merged_settings = DEFAULT_SETTINGS.copy()
                if "alarms" in loaded_settings:
                    for alarm_type in ["open", "close"]:
                        if alarm_type in loaded_settings["alarms"]:
                            merged_settings["alarms"][alarm_type].update(loaded_settings["alarms"][alarm_type])
                if "holidays" in loaded_settings:
                    merged_settings["holidays"] = loaded_settings["holidays"]
                return merged_settings
    except Exception as e:
        logger.error(f"설정 파일 로드 중 오류 발생: {e}")
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"설정 파일 저장 중 오류 발생: {e}")

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
    logger.info(f"메시지 전송 완료: {message}")

async def get_next_run_time(target_time):
    now = get_us_time()
    logger.info(f"현재 미국 시간: {now}")
    
    # 오늘 날짜에 설정된 시간을 결합 (미국 시간 기준)
    next_run = datetime.combine(now.date(), target_time)
    next_run = next_run.replace(tzinfo=edt)
    logger.info(f"다음 실행 시간 (미국): {next_run}")
    logger.info(f"다음 실행 시간 (한국): {next_run.astimezone(kst)}")
    
    # 현재 시간이 설정된 시간보다 늦으면 다음날로 설정
    if now > next_run:
        next_run += timedelta(days=1)
        logger.info(f"다음날로 설정됨 (미국): {next_run}")
        logger.info(f"다음날로 설정됨 (한국): {next_run.astimezone(kst)}")
    
    return next_run

def is_holiday(date):
    """주어진 날짜가 휴일인지 확인"""
    date_str = date.strftime("%Y-%m-%d")
    return date_str in settings["holidays"]

async def run_bot():
    logger.info("봇 시작됨")
    while True:
        try:
            for alarm_type in ["open", "close"]:
                try:
                    alarm_settings = settings["alarms"][alarm_type]
                    
                    if not alarm_settings["is_active"] or not alarm_settings["target_time"]:
                        logger.info(f"{alarm_type} 알람이 비활성화되어 있거나 시간이 설정되지 않음")
                        continue

                    us_now = get_us_time()
                    
                    # 주말 체크
                    if us_now.weekday() >= 5:
                        logger.info(f"미국 시간 기준 주말이므로 {alarm_type} 알람을 보내지 않습니다.")
                        continue
                        
                    # 휴일 체크
                    if is_holiday(us_now.date()):
                        logger.info(f"휴일이므로 {alarm_type} 알람을 보내지 않습니다.")
                        continue

                    target_time = datetime.strptime(alarm_settings["target_time"], "%H:%M").time()
                    next_run = await get_next_run_time(target_time)
                    now = get_us_time()
                    
                    wait_seconds = (next_run - now).total_seconds()
                    logger.info(f"{alarm_type} 대기 시간: {wait_seconds}초")
                    
                    # 수정된 시간 체크 로직
                    if -60 <= wait_seconds <= 60:  # 목표 시간 전후 1분 이내
                        if wait_seconds > 0:
                            await asyncio.sleep(wait_seconds)
                        # 최종 체크
                        us_now = get_us_time()
                        if us_now.weekday() >= 5 or is_holiday(us_now.date()):
                            continue
                        await send_daily_message(alarm_type)
                        # 메시지 전송 후 다음 날까지 대기
                        await asyncio.sleep(3600)  # 1시간 대기
                except Exception as e:
                    logger.error(f"{alarm_type} 알람 처리 중 오류 발생: {e}")
                    continue

            await asyncio.sleep(30)  # 30초마다 체크
        except asyncio.CancelledError:
            logger.warning("봇 태스크가 취소됨")
            raise
        except Exception as e:
            logger.error(f"봇 실행 중 예외 발생: {e}")
            await asyncio.sleep(5)  # 오류 발생 시 5초 대기 후 재시도

async def restart_bot():
    global bot_task
    if bot_task:
        bot_task.cancel()
    bot_task = asyncio.create_task(run_bot())
    logger.info("봇 재시작됨")

# 주기적으로 서버에 ping을 보내는 함수
def ping_server():
    while True:
        try:
            # HEAD 대신 GET 요청 사용
            response = requests.get(SERVER_URL, timeout=10, params={'ping': 'true'})
            if response.status_code == 200:
                logger.info("서버에 ping 전송 성공")
            else:
                logger.warning(f"서버 ping 응답 코드: {response.status_code}")
        except requests.Timeout:
            logger.error("서버 ping 타임아웃")
        except Exception as e:
            logger.error(f"ping 전송 중 오류 발생: {e}")
        time_module.sleep(600)

@app.on_event("startup")
async def startup_event():
    logger.info("서버 시작됨")
    # 시작 시 현재 시간 확인
    now = get_korea_time()
    logger.info(f"서버 시작 시간: {now}")
    
    # 현재 설정된 알람 시간 로깅
    open_time = settings["alarms"]["open"]["target_time"]
    close_time = settings["alarms"]["close"]["target_time"]
    open_kr_time = convert_time_to_kst(open_time)
    close_kr_time = convert_time_to_kst(close_time)
    
    logger.info(f"설정된 오픈 시간 - 미국: {open_time}, 한국: {open_kr_time}")
    logger.info(f"설정된 마감 시간 - 미국: {close_time}, 한국: {close_kr_time}")
    
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

def get_weekday_kr(date_str):
    """날짜 문자열을 받아서 한글 요일을 반환"""
    date = datetime.strptime(date_str, "%Y-%m-%d")
    weekdays = ["월", "화", "수", "목", "금", "토", "일"]
    return weekdays[date.weekday()]

def clean_past_holidays():
    """지난 날짜를 제거하고 남은 날짜를 정렬"""
    today = get_us_time().date()
    settings['holidays'] = sorted([
        date for date in settings['holidays']
        if datetime.strptime(date, "%Y-%m-%d").date() >= today
    ])
    save_settings(settings)

@app.get("/")
async def root(request: Request):
    # 지난 날짜 제거 및 정렬
    clean_past_holidays()
    
    # 현재 설정된 시간들의 한국 시간 변환값 계산
    open_kr_time = convert_time_to_kst(settings["alarms"]["open"]["target_time"])
    close_kr_time = convert_time_to_kst(settings["alarms"]["close"]["target_time"])
    
    # 휴일 목록에 요일 정보 추가
    holidays_with_weekday = [
        {"date": date, "weekday": get_weekday_kr(date)}
        for date in settings['holidays']
    ]
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request, 
            "settings": settings,
            "open_kr_time": open_kr_time,
            "close_kr_time": close_kr_time,
            "holidays_with_weekday": holidays_with_weekday
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
    logger.info(f"설정 업데이트: 오픈={open_time}, 마감={close_time}")
    
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
    logger.info(f"수동 메시지 전송 요청: {alarm_type}")
    await send_daily_message(alarm_type)
    return RedirectResponse(url="/", status_code=303)

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

@app.on_event("shutdown")
async def shutdown_event():
    logger.warning("서버 종료 이벤트 발생")
    try:
        if bot_task:
            logger.info("봇 태스크 정리 중...")
            bot_task.cancel()
            try:
                await bot_task
            except asyncio.CancelledError:
                logger.info("봇 태스크가 정상적으로 취소됨")
    except Exception as e:
        logger.error(f"서버 종료 중 오류 발생: {e}")

@app.get("/ping")
async def ping():
    return {"status": "ok"}

if __name__ == "__main__":
    try:
        uvicorn.run(
            "bot:app",
            host="0.0.0.0",
            port=PORT,
            reload=True,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"서버 실행 중 치명적 오류 발생: {e}")