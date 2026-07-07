import asyncio
import threading
import time

import requests
from fastapi import FastAPI
import uvicorn

import config
from bot import build_app

_status = {"running": False, "error": None, "attempt": 0}


def _run_bot_in_thread():
    """python-telegram-bot butuh event loop sendiri kalau dijalankan di thread terpisah.
    Retry TANPA BATAS dengan backoff (cap 60 detik) - koneksi ke Telegram dari Space
    gratis kadang tidak stabil di awal, tapi biasanya berhasil kalau terus dicoba."""
    attempt = 0
    while True:
        attempt += 1
        _status["attempt"] = attempt
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            application = build_app()
            _status["running"] = True
            _status["error"] = None
            application.run_polling(
                close_loop=False,
                stop_signals=None,
                drop_pending_updates=True,
            )
            return  # run_polling keluar normal (jarang, kecuali di-stop manual)
        except Exception as e:
            _status["running"] = False
            _status["error"] = f"(percobaan ke-{attempt}) {type(e).__name__}: {e}"
            time.sleep(min(10 * attempt, 60))  # backoff naik, maksimal 60 detik


bot_thread = threading.Thread(target=_run_bot_in_thread, daemon=True)
bot_thread.start()

api = FastAPI()


@api.get("/")
def status():
    if _status["running"]:
        return {"status": "ok", "detail": "Bot Telegram aktif dan siap menerima perintah.", "attempt": _status["attempt"]}
    return {"status": "retrying", "detail": _status["error"], "attempt": _status["attempt"]}


@api.get("/diagnostics")
def diagnostics():
    result = {"token_set": bool(config.TELEGRAM_BOT_TOKEN)}
    if not config.TELEGRAM_BOT_TOKEN:
        return result
    try:
        r = requests.get(
            f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/getMe",
            timeout=15,
        )
        result["getMe_status"] = r.status_code
        result["getMe_response"] = r.json()
    except Exception as e:
        result["getMe_error"] = f"{type(e).__name__}: {e}"
    return result


if __name__ == "__main__":
    uvicorn.run(api, host="0.0.0.0", port=7860, log_config=None)
