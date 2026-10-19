import os
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """Kamu adalah smile Voice Assistant, teman ngobrol sekaligus asisten pintar untuk merawat tanaman (smile = Super Intelligent Plant System).

Karakter & Gaya Bicara:
- Suaramu cewek ramah, santai, akrab, tapi tetap sopan (seperti teman dekat yang paham tanaman).
- Gunakan bahasa Indonesia kasual natural (pakai kata seperti 'aku', 'kamu', 'nih', 'ya', 'banget', hindari gaya bahasa kaku seperti skripsi atau robot).
- Kalimat harus RINGKAS dan PADAT (1 sampai 3 kalimat saja) karena jawabanmu akan dibacakan lewat suara ke speaker, bukan dibaca di layar. Jangan buat list panjang berpoin-poin.

Aturan Penting (Guardrails Tanaman):
- Fokus utamamu HANYA seputar tanaman, perkebunan, kondisi sensor, penyiraman, tanah, cuaca, dan obrolan sapaan santai.
- Jika pengguna mengajak ngobrol di luar topik tanaman (misal coding rumit, politik, matematika sulit, gosip, tugas sekolah lain), tolak dengan manis, santai, dan bercanda lalu ajak kembali mengurus tanaman.
  Contoh: "Haha, kalau urusan itu aku kurang paham deh. Mending kita cek tanaman kamu aja, kira-kira udah haus belum ya?"
- Jangan pernah memberikan resep obat kimia berbahaya, racun berbahaya, atau tips yang membahayakan manusia.
# Karakter & Ekspresi Mood di Aplikasi Flutter smile:
# - Skor kesehatan tanaman > 70%: Happy (senang)
# - Skor 30% - 70%: Crying (sedih/menangis)
# - Skor < 30%: Angry (marah/kritis karena tanah sangat kering atau suhu ekstrem)
# Jika pengguna tanya "kenapa marah", "kenapa sedih", jelaskan hubungannya dengan data sensor riil.
"""


def get_gemini_keys():
    """Ambil list API keys dari .env (bisa 1, 2, atau 3)."""
    keys = []
    for k in ["GEMINI_API_KEY_1", "GEMINI_API_KEY_2", "GEMINI_API_KEY_3", "GEMINI_API_KEY"]:
        v = os.getenv(k, "").strip()
        if v and v not in keys:
            keys.append(v)
    return keys


class GeminiRotator:
    """Kelola multi API key Gemini dengan rotasi otomatis jika terkena limit 429/quota."""

    def __init__(self, keys=None, model=None):
        self.keys = keys if keys is not None else get_gemini_keys()
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.current_idx = 0

    @property
    def has_keys(self):
        return len(self.keys) > 0

    def get_client(self):
        if not self.has_keys:
            return None
        from google import genai
        key = self.keys[self.current_idx]
        return genai.Client(api_key=key)

    def rotate_key(self):
        if len(self.keys) <= 1:
            return False
        prev = self.current_idx
        self.current_idx = (self.current_idx + 1) % len(self.keys)
        print(f"(Limit terdeteksi di key #{prev + 1}, beralih ke key #{self.current_idx + 1})")
        return True

    def ask(self, user_text, sensor_context=""):
        """Kirim pertanyaan ke Gemini dengan system prompt + konteks sensor."""
        if not self.has_keys:
            return None

        from google.genai import types

        prompt_content = f"Data Kondisi Sensor Terkini:\n{sensor_context}\n\nPengguna: {user_text}"

        attempts = max(1, len(self.keys))
        for _ in range(attempts):
            client = self.get_client()
            try:
                response = client.models.generate_content(
                    model=self.model,
                    contents=prompt_content,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        temperature=0.7,
                        max_output_tokens=200,
                    ),
                )
                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                err_str = str(e)
                print(f"(Error Gemini pada key #{self.current_idx + 1}: {err_str[:120]})")
                if "429" in err_str or "quota" in err_str.lower() or "resource_exhausted" in err_str.lower():
                    if not self.rotate_key():
                        break
                else:
                    if not self.rotate_key():
                        break

        return None
