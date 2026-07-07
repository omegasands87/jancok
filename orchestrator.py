import requests
import config

TIMEOUT = 30


def _call_openai_compatible(base_url, api_key, model, system_prompt, user_prompt):
    """Dipakai untuk Groq, Cerebras, OpenRouter (semuanya OpenAI-compatible schema)."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.8,
        "max_tokens": 700,
    }
    r = requests.post(base_url, headers=headers, json=payload, timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"].strip()


def _call_groq(system_prompt, user_prompt):
    return _call_openai_compatible(
        "https://api.groq.com/openai/v1/chat/completions",
        config.GROQ_API_KEY, config.GROQ_MODEL, system_prompt, user_prompt,
    )


def _call_cerebras(system_prompt, user_prompt):
    return _call_openai_compatible(
        "https://api.cerebras.ai/v1/chat/completions",
        config.CEREBRAS_API_KEY, config.CEREBRAS_MODEL, system_prompt, user_prompt,
    )


def _call_openrouter_hermes(system_prompt, user_prompt):
    return _call_openai_compatible(
        "https://openrouter.ai/api/v1/chat/completions",
        config.OPENROUTER_API_KEY, config.OPENROUTER_MODEL, system_prompt, user_prompt,
    )


def _call_gemini(system_prompt, user_prompt):
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{config.GEMINI_MODEL}:generateContent?key={config.GEMINI_API_KEY}"
    )
    payload = {
        "contents": [{"parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]}],
    }
    r = requests.post(url, json=payload, timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json()
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()


def _call_cohere(system_prompt, user_prompt):
    headers = {
        "Authorization": f"Bearer {config.COHERE_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": config.COHERE_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    r = requests.post("https://api.cohere.com/v2/chat", headers=headers, json=payload, timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json()
    return data["message"]["content"][0]["text"].strip()


# Urutan fallback: Hermes (OpenRouter) diprioritaskan sesuai request awal,
# lalu Groq/Cerebras (cepat), lalu Gemini, lalu Cohere.
PROVIDER_CHAIN = [
    ("OpenRouter-Hermes", _call_openrouter_hermes, lambda: bool(config.OPENROUTER_API_KEY)),
    ("Groq", _call_groq, lambda: bool(config.GROQ_API_KEY)),
    ("Cerebras", _call_cerebras, lambda: bool(config.CEREBRAS_API_KEY)),
    ("Gemini", _call_gemini, lambda: bool(config.GEMINI_API_KEY)),
    ("Cohere", _call_cohere, lambda: bool(config.COHERE_API_KEY)),
]


def generate_text(system_prompt: str, user_prompt: str) -> str:
    """Coba tiap provider berurutan. Kalau satu gagal/limit habis, lanjut ke berikutnya."""
    errors = []
    for name, fn, has_key in PROVIDER_CHAIN:
        if not has_key():
            continue
        try:
            result = fn(system_prompt, user_prompt)
            if result:
                return result
        except Exception as e:
            errors.append(f"{name}: {e}")
            continue
    raise RuntimeError(
        "Semua provider LLM gagal atau belum diset API key-nya.\n" + "\n".join(errors)
    )


def agent_script_writer(topic: str, platform: str) -> str:
    system = (
        "Kamu adalah copywriter konten sosial media profesional. "
        "Tulis dalam Bahasa Indonesia, gaya singkat, tajam, engaging, sesuai platform yang diminta. "
        "Output HANYA teks caption/hook siap pakai, tanpa penjelasan tambahan."
    )
    user = f"Buat caption/hook konten untuk platform {platform} dengan topik: {topic}"
    return generate_text(system, user)


def agent_image_prompt_writer(topic: str, caption: str) -> str:
    system = (
        "Kamu adalah prompt engineer untuk text-to-image AI. "
        "Buat SATU prompt visual (dalam Bahasa Inggris) untuk background image bergaya minimalis, "
        "aesthetic, warna soft/kontras enak dilihat, cocok jadi background quote/content card ala akun "
        "instagram estetik (seperti syntaix.ai). JANGAN sertakan teks apapun di dalam gambar. "
        "Output HANYA prompt-nya, satu baris, tanpa penjelasan."
    )
    user = f"Topik konten: {topic}\nCaption: {caption}"
    return generate_text(system, user)
