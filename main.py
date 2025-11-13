import time
import requests
import os

# ============================
#   CONFIG (Render variables)
# ============================

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

def send_telegram_message(text: str):
    """Envoie un message dans Telegram et affiche les erreurs."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ ERROR: Missing TOKEN or CHAT_ID in environment variables")
        print(f"TOKEN found: {bool(TELEGRAM_BOT_TOKEN)}")
        print(f"CHAT_ID found: {bool(TELEGRAM_CHAT_ID)}")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}

    try:
        resp = requests.post(url, data=payload)
        print("Telegram response:", resp.text)
    except Exception as e:
        print("❌ Telegram send failed:", e)


def start_bot():
    print("🤖 Bot Chasseur de Trésors lancé ! Scan toutes les 20 sec.")
    send_telegram_message("🤖 Bot Chasseur de Trésors lancé ! Scan toutes les 20 sec.")

    while True:
        print("Scan finished.")
        time.sleep(20)


if __name__ == "__main__":
    print("🚀 Starting bot...")
    start_bot()
