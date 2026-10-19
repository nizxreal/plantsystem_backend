# smile Voice Assistant

Proyek voice assistant AI untuk sistem irigasi tanaman pintar (smile = Super Intelligent Plant System).
Ngomong soal tanaman, baca sensor dari ESP32 via Firebase RTDB, kontrol pompa, dan ngobrol santai pakai Gemini LLM.

## Fitur
- Speech-to-Text (Google) → ngerti suara kamu
- LLM (Gemini 2.5 Flash) → otak AI, ngobrol soal tanaman
- Text-to-Speech (Edge-TTS) → suara cewek santai `id-ID-GadisNeural`
- Firebase RTDB → baca sensor (temp, humidity, soil_moisture, ph), kontrol pompa
- Intent Router → nyalakan/pompa/matikan pompa, cek status, tips tanaman
- Rotasi API Key → 2-3 akun mencegah rate limit
- Local Knowledge Base → jawaban tanaman tanpa butuh API key

## Struktur File
- `assistant_ai.py` — main loop (Listen-Think-Act-Speak)
- `firebase_client.py` — akses Firebase RTDB (get sensors, set actuators)
- `llm_client.py` — Gemini LLM + system prompt + rotasi API key
- `intent.py` — intent router + local knowledge base (tips tanaman, pupuk, hama, dll)
- `demo_conversations.py` — demo 7 pertanyaan tanpa butuh mikrofon/API key
- `setup.py` — install semua dependencies otomatis
- `requirements.txt` — daftar library Python
- `RASPBERRY_PI_SETUP.txt` — panduan transfer ke Raspberry Pi
- `.env` — API key, Firebase URL, konfigurasi voice (di `.gitignore`)

## Cara Pakai

### 1. Install Dependencies
```bash
python setup.py
```
Atau:
```bash
pip install -r requirements.txt
```

### 2. Konfigurasi API Key
Edit `.env` (buat dari `.env.example` jika ada):
```env
FIREBASE_URL=https://linoplantsys-default-rtdb.asia-southeast1.firebasedatabase.app
GEMINI_API_KEY_1=***
GEMINI_API_KEY_2=***
GEMINI_API_KEY_3=***
GEMINI_MODEL=gemini-2.5-flash
TTS_VOICE=id-ID-GadisNeural
```

Dapatkan API key Gemini di: https://aistudio.google.com/app/apikey

### 3. Test Demo (tanpa mikrofon)
```bash
python demo_conversations.py
```
Lihat 7 contoh pertanyaan: kondisi tanaman, tips cabai, pupuk, hama, dll.

### 4. Pakai Voice Assistant
```bash
python assistant_ai.py
```
Rekam pertanyaan → STT → intent router → jawaban (lokal/LLM) → TTS → speak.

## Contoh Percakapan
- "Tanamanku kabarnya gimana?"
- "Kenapa kamu marah?"
- "Tanah kering harus gimana?"
- "Tips cabai sehat"
- "Nyalakan pompa"
- "Matikan pompa kabut"

## Topik yang Didukung
- Tanaman, sensor, tanah, penyiraman
- Tips perawatan (pupuk, hama, penyakit)
- Kontrol pompa air & pengabutan
- Mood tanaman (Happy/Crying/Angry berdasarkan skor sensor)

## Arsitektur
```
Suara (mic) → STT (Google) → Intent Router
                                  ├── Actuator control → Firebase RTDB → Pompa
                                  ├── Sensor report → Firebase RTDB → Baca sensor
                                  ├── Local knowledge → Tips tanaman offline
                                  └── Gemini LLM → Chat + analisa mood → TTS (Edge-TTS)
```

## Voice Configuration
- Voice: `id-ID-GadisNeural` (cewek, santai)
- Rate: `+5%` (natur)
- Pitch: `+0Hz` (default)
- Cek semua voice Indonesia: `edge-tts --list-voices | grep "id-ID"`

## Push ke GitHub
Lihat `GIT_PUSH_GUIDE.txt` untuk panduan lengkap.

---
Project smile - Super Intelligent Plant System
Arfalindo Nova Hidayat - SMK Leonardo Klaten
