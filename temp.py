# import logging
# import os
# from dotenv import load_dotenv
# from telegram import Update
# from telegram.ext import Updater, Application, CommandHandler, MessageHandler, filters, ContextTypes

# # 환경 변수 로드
# load_dotenv()

# # 로깅 설정
# logging.basicConfig(
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
#     level=logging.INFO
# )

# # 봇 토큰 (BotFather에서 생성한 토큰을 입력)
# BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
# # # 봇 토큰과 채널 ID
# # TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
# CHANNEL_ID = int(os.getenv('TELEGRAM_CHANNEL_ID'))  # 문자열을 정수로 변환


# class TelegramBot:
#     def __init__(self, name, token):
#         self.core = telegram.Bot(token)
#         self.updater = Updater(token)
#         self.id = CHANNEL_ID
#         self.name = name

#     def sendMessage(self, text):
#         self.core.sendMessage(chat_id = self.id, text=text)

#     def stop(self):
#         self.updater.start_polling()
#         self.updater.dispatcher.stop()
#         self.updater.job_queue.stop()
#         self.updater.stop()


# class BotChii(TelegramBot):
#     def __init__(self):
#         self.token = BOT_TOKEN
#         TelegramBot.__init__(self, '치이', self.token)
#         self.updater.stop()

#     def add_handler(self, cmd, func):
#         self.updater.dispatcher.add_handler(CommandHandler(cmd, func))

#     def start(self):
#         self.sendMessage('치이 봇이 잠에서 깨어납니다.')
#         self.updater.start_polling()
#         self.updater.idle()

# def proc_rolling(bot, update):
#     chii.sendMessage('데구르르..')
#     sound = firecracker()
#     chii.sendMessage(sound)
#     chii.sendMessage('르르..')

# def proc_stop(bot, update):
#     chii.sendMessage('치이 봇이 잠듭니다.')
#     chii.stop()

# def firecracker():
#     return '팡팡!'

# chii = ChatBotModel.BotChii()
# chii.add_handler('rolling', proc_rolling)
# chii.add_handler('stop', proc_stop)
# chii.start()


# # 활성화할 특정 채팅방 ID (그룹 또는 개인 채팅 ID)
# # ALLOWED_CHAT_ID = int(os.getenv('TELEGRAM_CHANNEL_ID'))  # 그룹 채팅 ID (음수로 시작)
# # 개인 채팅의 경우 양수로 시작하는 ID를 입력
# # async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
# #     """사용자가 /start 명령어를 입력했을 때 응답"""
# #     await context.bot.send_message(
# #         chat_id=CHANNEL_ID,
# #         text='안녕하세요! 미장 알림 봇입니다.\n'
# #         )
#     # chat = update.effective_chat  # 현재 메시지가 발생한 채팅방 정보
    
#     # # 봇이 관리자인지 확인
#     # bot_member = await context.bot.get_chat_member(chat.id, context.bot.id)
#     # if bot_member.status in ["administrator", "creator"]:
#     #     # 봇이 관리자인 경우 응답
#     #     await update.message.reply_text(f"안녕하세요! 이 방({chat.title})에서 활성화되었습니다.")
#     # else:
#     #     # 봇이 관리자가 아닌 경우 응답하지 않음
#     #     logging.info(f"봇은 이 채팅방({chat.id})에서 관리자가 아닙니다.")

# # def main() -> None:
# #     """봇 실행"""
# #     # 텔레그램 애플리케이션 생성
# #     application = Application.builder().token(BOT_TOKEN).build()

# #     # /start 명령어 핸들러 등록
# #     application.add_handler(CommandHandler("start", start))

# #     # 봇 실행
# #     application.run_polling()

# # if __name__ == "__main__":
# #     main()



# # import os
# # import logging
# # from datetime import datetime
# # import pytz
# # from dotenv import load_dotenv
# # from telegram import Update
# # from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
# # from apscheduler.schedulers.asyncio import AsyncIOScheduler
# # from apscheduler.triggers.cron import CronTrigger

# # # 환경 변수 로드
# # load_dotenv()

# # # 로깅 설정
# # logging.basicConfig(
# #     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
# #     level=logging.INFO
# # )
# # logger = logging.getLogger(__name__)

# # # 봇 토큰과 채널 ID
# # TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
# # CHANNEL_ID = int(os.getenv('TELEGRAM_CHANNEL_ID'))  # 문자열을 정수로 변환

# # # 미장 시간대 설정 (서머타임 자동 적용)
# # KST = pytz.timezone('Asia/Seoul')

# # # 미장 시작/종료 시간
# # MARKET_OPEN = "09:00"
# # MARKET_CLOSE = "15:30"

# # async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
# #     """봇 시작 명령어 처리"""
# #     # 명령어를 입력한 채팅방에 응답
# #     await update.message.reply_text(
# #         '안녕하세요! 미장 알림 봇입니다.\n'
# #         '이 채팅방에서 미장 시작(09:00)과 종료(15:30) 시간에 알림을 보내드립니다.'
# #     )
    
# #     # 채널에도 시작 메시지 전송
# #     try:
# #         await context.bot.send_message(
# #             chat_id=CHANNEL_ID,
# #             text='안녕하세요! 미장 알림 봇입니다.\n'
# #                  '이 채널에서 미장 시작(09:00)과 종료(15:30) 시간에 알림을 보내드립니다.'
# #         )
# #     except Exception as e:
# #         logger.error(f"채널 메시지 전송 실패: {e}")

# # async def send_market_notification(context: ContextTypes.DEFAULT_TYPE, message: str):
# #     """시장 알림 전송"""
# #     job = context.job
# #     try:
# #         await context.bot.send_message(job.chat_id, text=message)
# #     except Exception as e:
# #         logger.error(f"알림 전송 실패: {e}")

# # async def set_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
# #     """알림 설정"""
# #     chat_id = CHANNEL_ID  # 채널 ID 사용
    
# #     # 그룹 채팅방에서 관리자만 설정 가능
# #     if chat_type != 'private':
# #         user = await context.bot.get_chat_member(chat_id, update.effective_user.id)
# #         if user.status not in ['creator', 'administrator']:
# #             await update.message.reply_text('죄송합니다. 그룹 채팅방에서는 관리자만 알림을 설정할 수 있습니다.')
# #             return
    
# #     # 기존 작업 제거
# #     if 'scheduler' in context.bot_data:
# #         context.bot_data['scheduler'].remove_all_jobs()
    
# #     # 새로운 스케줄러 생성
# #     scheduler = AsyncIOScheduler()
# #     context.bot_data['scheduler'] = scheduler
    
# #     # 미장 시작 알림
# #     scheduler.add_job(
# #         send_market_notification,
# #         CronTrigger(hour=9, minute=0),
# #         args=[context, "🔔 미장이 시작되었습니다!"],
# #         id=f'open_{chat_id}',
# #         chat_id=chat_id  # 채널로 메시지 전송
# #     )
    
# #     # 미장 종료 알림
# #     scheduler.add_job(
# #         send_market_notification,
# #         CronTrigger(hour=15, minute=30),
# #         args=[context, "🔔 미장이 종료되었습니다!"],
# #         id=f'close_{chat_id}',
# #         chat_id=chat_id  # 채널로 메시지 전송
# #     )
    
# #     scheduler.start()
# #     await update.message.reply_text('알림이 설정되었습니다!')

# # async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
# #     """도움말 명령어 처리"""
# #     help_text = (
# #         "📚 미장 알림 봇 사용법\n\n"
# #         "/start - 봇 시작\n"
# #         "/set - 알림 설정 (그룹에서는 관리자만 가능)\n"
# #         "/help - 도움말 보기\n\n"
# #         "매일 09:00와 15:30에 자동으로 알림이 전송됩니다."
# #     )
# #     await update.message.reply_text(help_text)

# # def main():
# #     """봇 실행"""
# #     application = Application.builder().token(TOKEN).build()
    
# #     # 봇의 기본 데이터에 채널 ID 저장
# #     application.bot_data['default_channel'] = CHANNEL_ID
    
# #     # 명령어 핸들러 등록
# #     application.add_handler(CommandHandler("start", start))
# #     application.add_handler(CommandHandler("set", set_notifications))
# #     application.add_handler(CommandHandler("help", help_command))
    
# #     # 봇 실행
# #     application.run_polling(allowed_updates=Update.ALL_TYPES)

# # if __name__ == '__main__':
# #     main() 