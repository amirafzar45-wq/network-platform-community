import requests
from app.core.config import settings

def notify_telegram(message: str):
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        return
    try:
        requests.post(f'https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage',
                      json={'chat_id': settings.telegram_chat_id, 'text': message}, timeout=8)
    except Exception:
        pass
