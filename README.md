---
title: Content Orchestrator Bot
emoji: 🤖
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# Multi-Agent Content Orchestrator (Telegram Bot)

Bot Telegram yang meng-orkestrasi beberapa agent LLM (Hermes via OpenRouter, dengan
fallback Groq / Cerebras / Gemini / Cohere) untuk membuat **caption + gambar konten**
TikTok/YouTube/Instagram, digabung otomatis jadi satu content card, dengan pilihan
aspect ratio.

## Cara Deploy ke HuggingFace Spaces

1. Buat Space baru di huggingface.co/new-space
   - SDK: **Docker** (sudah di-set otomatis lewat `sdk: docker` di header README ini + `Dockerfile`)
   - Visibility bebas (public/private)
2. Upload semua file di folder ini ke Space (via web UI drag-drop, atau `git push`).
3. Buka tab **Settings > Variables and secrets** di Space kamu, tambahkan sebagai **Secret**:

   | Nama Secret          | Wajib? | Keterangan                              |
   |-----------------------|--------|------------------------------------------|
   | `TELEGRAM_BOT_TOKEN`  | Wajib  | Dari @BotFather                          |
   | `OPENROUTER_API_KEY`  | Disarankan | Untuk akses model Hermes              |
   | `GROQ_API_KEY`        | Opsional (fallback) |                              |
   | `CEREBRAS_API_KEY`    | Opsional (fallback) |                              |
   | `GEMINI_API_KEY`      | Opsional (fallback) |                              |
   | `COHERE_API_KEY`      | Opsional (fallback) |                              |
   | `HF_TOKEN`            | Opsional | Fallback image-gen kalau Pollinations down |

   Minimal harus ada `TELEGRAM_BOT_TOKEN` + minimal **satu** API key LLM di atas.

4. Space akan otomatis build & restart (build Docker sedikit lebih lama, ~2-3 menit).
   Cek tab **Logs > Container** — kalau tidak ada error, bot sudah jalan.
   Kamu juga bisa buka URL Space-nya langsung di browser: akan muncul JSON
   `{"status": "ok", "detail": "Bot Telegram aktif dan siap menerima perintah."}`.
5. Buka Telegram, chat bot kamu, kirim:
   ```
   tips produktivitas pagi hari, tiktok, rasio 9:16
   ```
   Bot akan balas gambar + caption jadi satu.

## Format perintah di Telegram

```
<topik bebas>, <platform: tiktok/youtube/ig>, rasio <1:1|4:5|9:16|16:9>
```
Semua bagian opsional kecuali topik. Default platform = Instagram, default rasio = 4:5.

## Supaya hasil visual lebih bagus (opsional tapi disarankan)

Font default PIL sangat basic. Download font `.ttf` (mis. Poppins-Bold, Montserrat-Bold)
lalu taruh di folder `fonts/` sebelum upload ke Space — compositor otomatis pakai font
tersebut kalau ada.

## ⚠️ Keterbatasan yang perlu kamu tahu (free tier)

1. **Mode bot: webhook** (bukan polling) — dipilih justru untuk MENGHINDARI masalah
   koneksi long-polling yang tidak stabil di Space gratis. Space hanya perlu menerima
   1 request dari Telegram tiap ada pesan masuk, tidak perlu jaga koneksi lama.
2. Kalau Space kamu tidak menyediakan env var `SPACE_HOST` otomatis (jarang, tapi bisa
   terjadi tergantung konfigurasi), tambahkan Secret manual **`PUBLIC_URL`** berisi
   URL Space kamu, contoh: `https://username-spacename.hf.space`.
3. **Rate limit tiap API gratisan berbeda-beda** — kalau satu provider habis limit,
   sistem otomatis fallback ke provider berikutnya di `orchestrator.py`
   (urutan: OpenRouter/Hermes → Groq → Cerebras → Gemini → Cohere).
4. **Generate video** belum termasuk di versi ini — video-gen AI gratis yang stabil
   nyaris tidak ada. Bisa dikembangkan lanjut pakai template motion (bukan AI) kalau perlu.
5. **Slug model OpenRouter/Cerebras/Groq bisa berubah** sewaktu-waktu. Kalau ada error
   "model not found", update env var `OPENROUTER_MODEL` / `GROQ_MODEL` / `CEREBRAS_MODEL`
   di Secrets sesuai model terbaru yang tersedia di masing-masing provider.
6. Cek `/diagnostics` kapan saja untuk lihat status token & webhook (apakah Telegram
   sudah tahu URL Space kamu dengan benar).

## Struktur file

```
Dockerfile        -> definisi environment (Python 3.11 slim)
app.py           -> entrypoint HF Space (jalankan bot + endpoint status FastAPI)
bot.py            -> handler Telegram
orchestrator.py   -> agent teks (caption + image-prompt writer), fallback chain LLM
image_gen.py      -> agent gambar (Pollinations, fallback HF Inference API)
compositor.py     -> gabung gambar + teks jadi content card
config.py         -> load semua API key dari environment
fonts/            -> taruh font .ttf di sini (opsional)
```
