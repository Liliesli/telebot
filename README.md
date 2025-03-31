# 미장 알림 텔레그램 봇

매일 미장 시작(09:00)과 종료(15:30) 시간에 텔레그램으로 알림을 보내주는 봇입니다.

## 기능

- 매일 미장 시작 시간(09:00) 알림
- 매일 미장 종료 시간(15:30) 알림
- 서머타임 자동 적용
- 무료 호스팅 지원 (Render.com)

## 설정 방법

1. 텔레그램 봇 생성
   - [@BotFather](https://t.me/botfather)에서 새 봇 생성
   - 받은 봇 토큰을 `.env` 파일에 입력

2. 환경 설정
   ```bash
   # 가상환경 생성 및 활성화
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate

   # 필요한 패키지 설치
   pip install -r requirements.txt
   ```

3. 봇 실행
   ```bash
   python bot.py
   ```

## Render.com 배포 방법

1. Render.com 계정 생성
2. New Web Service 선택
3. GitHub 저장소 연결
4. 다음 설정 적용:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python bot.py`
   - Environment Variables에 `TELEGRAM_BOT_TOKEN` 추가

## 사용 방법

1. 텔레그램에서 봇 검색 후 시작
2. `/start` 명령어로 봇 시작
3. `/set` 명령어로 알림 설정

## 주의사항

- 서버 시간대는 UTC로 설정되어 있으며, 봇이 자동으로 한국 시간으로 변환합니다.
- 서머타임은 자동으로 적용됩니다.
- 무료 호스팅의 경우 서버가 일시적으로 중단될 수 있습니다. 