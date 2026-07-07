import io
import logging
import re

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from telegram.request import HTTPXRequest

import config
from orchestrator import agent_script_writer, agent_image_prompt_writer
from image_gen import generate_image
from compositor import compose_card

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ASPECT_PATTERN = re.compile(r"\b(1:1|4:5|9:16|16:9)\b")
PLATFORM_KEYWORDS = {
    "tiktok": "TikTok",
    "youtube": "YouTube Shorts",
    "yt": "YouTube Shorts",
    "ig": "Instagram",
    "instagram": "Instagram",
}


def _parse_request(text: str):
    aspect_match = ASPECT_PATTERN.search(text)
    aspect_ratio = aspect_match.group(1) if aspect_match else config.DEFAULT_ASPECT

    platform = "Instagram"  # default
    lowered = text.lower()
    for kw, label in PLATFORM_KEYWORDS.items():
        if kw in lowered:
            platform = label
            break

    # bersihkan topic dari kata kunci rasio & platform biar prompt LLM bersih
    topic = ASPECT_PATTERN.sub("", text)
    for kw in PLATFORM_KEYWORDS:
        topic = re.sub(kw, "", topic, flags=re.IGNORECASE)
    topic = topic.strip(" ,.-") or text.strip()

    return topic, platform, aspect_ratio


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Halo! Kirim topik kontenmu, contoh:\n\n"
        "tips produktivitas pagi hari, tiktok, rasio 9:16\n\n"
        "Aku akan generate caption + gambar dan gabungkan otomatis.\n"
        "Rasio yang didukung: 1:1, 4:5, 9:16, 16:9 (default 4:5)."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    topic, platform, aspect_ratio = _parse_request(text)

    status_msg = await update.message.reply_text("⏳ Menulis caption...")

    try:
        caption = agent_script_writer(topic, platform)
        await status_msg.edit_text("⏳ Menyusun prompt visual...")

        image_prompt = agent_image_prompt_writer(topic, caption)
        await status_msg.edit_text("⏳ Generate gambar...")

        bg_image = generate_image(image_prompt, aspect_ratio)
        await status_msg.edit_text("⏳ Menggabungkan teks + gambar...")

        final_image = compose_card(bg_image, caption)

        buf = io.BytesIO()
        final_image.save(buf, format="JPEG", quality=95)
        buf.seek(0)

        # Kirim hasil DULU sebagai pesan baru (plain text, tanpa parse_mode -> anti-error
        # dari karakter spesial hasil LLM), baru hapus status setelah sukses terkirim.
        await update.message.reply_photo(
            photo=buf,
            caption=f"{platform} | rasio {aspect_ratio}\n\n{caption}",
        )
        await status_msg.delete()
    except Exception as e:
        logger.exception("Gagal proses request")
        try:
            await status_msg.edit_text(f"❌ Gagal: {e}")
        except Exception:
            # kalau status_msg sudah tidak valid/dihapus, kirim pesan baru supaya user tetap tahu
            await update.message.reply_text(f"❌ Gagal: {e}")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Global error handler - supaya error tak terduga tetap tercatat & (kalau memungkinkan) terlihat user."""
    logger.error("Unhandled exception", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(f"❌ Terjadi error tak terduga: {context.error}")
        except Exception:
            pass


def build_app() -> Application:
    if not config.TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN belum diset di environment/secrets.")

    request = HTTPXRequest(
        connect_timeout=30.0,
        read_timeout=30.0,
        write_timeout=30.0,
        pool_timeout=30.0,
    )
    app = (
        Application.builder()
        .token(config.TELEGRAM_BOT_TOKEN)
        .request(request)
        .get_updates_request(request)
        .build()
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)
    return app
