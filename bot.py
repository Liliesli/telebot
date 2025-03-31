import os
import logging
from datetime import datetime
import pytz
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 봇 토큰
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# 미장 시간대 설정 (서머타임 자동 적용)
KST = pytz.timezone('Asia/Seoul')

# 미장 시작/종료 시간
MARKET_OPEN = "09:00"
MARKET_CLOSE = "15:30"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """봇 시작 명령어 처리"""
    await update.message.reply_text(
        '안녕하세요! 미장 알림 봇입니다.\n'
        '매일 미장 시작(09:00)과 종료(15:30) 시간에 알림을 보내드립니다.'
    )

async def send_market_notification(context: ContextTypes.DEFAULT_TYPE, message: str):
    """시장 알림 전송"""
    job = context.job
    await context.bot.send_message(job.chat_id, text=message)

async def set_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """알림 설정"""
    chat_id = update.effective_chat.id
    
    # 기존 작업 제거
    if 'scheduler' in context.bot_data:
        context.bot_data['scheduler'].remove_all_jobs()
    
    # 새로운 스케줄러 생성
    scheduler = AsyncIOScheduler()
    context.bot_data['scheduler'] = scheduler
    
    # 미장 시작 알림
    scheduler.add_job(
        send_market_notification,
        CronTrigger(hour=9, minute=0),
        args=[context, "🔔 미장이 시작되었습니다!"],
        id=f'open_{chat_id}',
        chat_id=chat_id
    )
    
    # 미장 종료 알림
    scheduler.add_job(
        send_market_notification,
        CronTrigger(hour=15, minute=30),
        args=[context, "🔔 미장이 종료되었습니다!"],
        id=f'close_{chat_id}',
        chat_id=chat_id
    )
    
    scheduler.start()
    await update.message.reply_text('알림이 설정되었습니다!')

def main():
    """봇 실행"""
    application = Application.builder().token(TOKEN).build()
    
    # 명령어 핸들러 등록
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("set", set_notifications))
    
    # 봇 실행
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main() 