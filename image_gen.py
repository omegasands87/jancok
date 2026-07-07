import io
import urllib.parse
import requests
from PIL import Image

import config

TIMEOUT = 60


def _pollinations(prompt: str, width: int, height: int) -> Image.Image:
    """Gratis, tanpa API key. https://pollinations.ai"""
    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&nologo=true"
    r = requests.get(url, timeout=TIMEOUT)
    r.raise_for_status()
    return Image.open(io.BytesIO(r.content)).convert("RGB")


def _hf_inference(prompt: str, width: int, height: int) -> Image.Image:
    """Fallback: HuggingFace Inference API (butuh HF_TOKEN, ada limit gratis)."""
    if not config.HF_TOKEN:
        raise RuntimeError("HF_TOKEN belum diset, fallback HF Inference tidak bisa dipakai.")
    url = f"https://api-inference.huggingface.co/models/{config.HF_IMAGE_MODEL}"
    headers = {"Authorization": f"Bearer {config.HF_TOKEN}"}
    payload = {"inputs": prompt}
    r = requests.post(url, headers=headers, json=payload, timeout=TIMEOUT)
    r.raise_for_status()
    img = Image.open(io.BytesIO(r.content)).convert("RGB")
    return img.resize((width, height))


def generate_image(prompt: str, aspect_ratio: str) -> Image.Image:
    width, height = config.ASPECT_RATIOS.get(aspect_ratio, config.ASPECT_RATIOS[config.DEFAULT_ASPECT])
    try:
        return _pollinations(prompt, width, height)
    except Exception:
        return _hf_inference(prompt, width, height)
