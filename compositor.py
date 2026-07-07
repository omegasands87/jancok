import os
import textwrap
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONT_DIR = os.path.join(os.path.dirname(__file__), "fonts")


def _load_font(size: int, bold: bool = True):
    """Cari font .ttf di folder fonts/. Kalau tidak ada, pakai default PIL (kurang bagus,
    disarankan tambahkan font sendiri, mis. fonts/Poppins-Bold.ttf, untuk hasil terbaik)."""
    candidates = []
    if os.path.isdir(FONT_DIR):
        for f in os.listdir(FONT_DIR):
            if f.lower().endswith(".ttf"):
                if bold and "bold" in f.lower():
                    candidates.insert(0, f)
                else:
                    candidates.append(f)
    if candidates:
        try:
            return ImageFont.truetype(os.path.join(FONT_DIR, candidates[0]), size)
        except Exception:
            pass
    return ImageFont.load_default()


def _add_dark_overlay(img: Image.Image, opacity: int = 110) -> Image.Image:
    overlay = Image.new("RGBA", img.size, (0, 0, 0, opacity))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


def compose_card(background: Image.Image, text: str) -> Image.Image:
    """Overlay teks caption/hook di atas background image, rapi & center."""
    img = background.copy()
    width, height = img.size

    img = _add_dark_overlay(img, opacity=100)
    draw = ImageDraw.Draw(img)

    font_size = max(28, width // 16)
    font = _load_font(font_size)

    # wrap text supaya muat lebar gambar
    max_chars_per_line = max(10, width // (font_size // 2))
    wrapped = textwrap.fill(text, width=max_chars_per_line)
    lines = wrapped.split("\n")

    # hitung total tinggi blok teks
    line_heights = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_heights.append(bbox[3] - bbox[1])
    spacing = int(font_size * 0.35)
    total_text_height = sum(line_heights) + spacing * (len(lines) - 1)

    y = (height - total_text_height) // 2

    for line, lh in zip(lines, line_heights):
        bbox = draw.textbbox((0, 0), line, font=font)
        line_width = bbox[2] - bbox[0]
        x = (width - line_width) // 2
        # stroke tipis biar teks tetap terbaca di background apapun
        draw.text((x, y), line, font=font, fill="white",
                   stroke_width=max(1, font_size // 20), stroke_fill="black")
        y += lh + spacing

    return img
