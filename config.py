import os

# === Telegram ===
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

# === LLM Providers (urutan fallback: GROQ -> CEREBRAS -> OPENROUTER(Hermes) -> GEMINI -> COHERE) ===
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

CEREBRAS_API_KEY = os.environ.get("CEREBRAS_API_KEY", "")
CEREBRAS_MODEL = os.environ.get("CEREBRAS_MODEL", "llama3.1-8b")

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
# Model Hermes (Nous Research) via OpenRouter. Cek slug terbaru di openrouter.ai/models
# jika model ini sudah deprecated/berubah nama.
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "nousresearch/hermes-3-llama-3.1-405b:free")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")

COHERE_API_KEY = os.environ.get("COHERE_API_KEY", "")
COHERE_MODEL = os.environ.get("COHERE_MODEL", "command-r")

# === Image Generation ===
# Default: Pollinations.ai (gratis, tanpa API key, tanpa limit ketat)
HF_TOKEN = os.environ.get("HF_TOKEN", "")  # opsional, untuk fallback ke HF Inference API (SDXL/FLUX)
HF_IMAGE_MODEL = os.environ.get("HF_IMAGE_MODEL", "black-forest-labs/FLUX.1-schnell")

# === Aspect ratio presets (width, height) ===
ASPECT_RATIOS = {
    "1:1": (1080, 1080),
    "4:5": (1080, 1350),
    "9:16": (1080, 1920),
    "16:9": (1920, 1080),
}
DEFAULT_ASPECT = "4:5"
