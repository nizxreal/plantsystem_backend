# SIPS Voice Assistant - Test Audio & TTS

Proyek untuk testing audio (mic + speaker) dan Text-to-Speech di PC Windows, 
kemudian copy ke Raspberry Pi 4/5 untuk sistem SIPS Plant Monitoring.

## Struktur File

- `requirements.txt` - Dependencies Python
- `setup.py` - Install dependencies otomatis
- `audio_test.py` - Test mic dan speaker (rekam + playback)
- `tts_test.py` - Test Text-to-Speech (Edge-TTS dan pyttsx3)

## Cara Pakai di PC Windows

### 1. Install Dependencies

Buka terminal (git bash) di folder ini, lalu jalankan:

```bash
python setup.py
```

Atau manual:

```bash
pip install -r requirements.txt
```

### 2. Test Audio (Mic + Speaker)

```bash
python audio_test.py
```

Skrip ini akan:
- Tampilkan daftar device audio
- Rekam suara 5 detik dari mic
- Putar balik ke speaker
- Simpan file test_recording.wav

### 3. Test Text-to-Speech

```bash
python tts_test.py
```

Skrip ini akan test 2 TTS engine:
- Edge-TTS (Microsoft, butuh internet, suara natural)
- pyttsx3 (offline, suara robot)

## Copy ke Raspberry Pi

Setelah test berhasil di PC, copy folder ini ke Raspberry Pi:

### Via USB Stick
1. Copy folder sips-voice-assistant ke USB
2. Colok ke Raspberry Pi
3. Copy ke /home/pi/

### Via Git (jika sudah push ke GitHub)
```bash
git clone <repo-url>
cd sips-voice-assistant
python3 setup.py
```

### Via SCP (jika PC dan RPi di WiFi sama)
```bash
scp -r D:/Arfalindo/sips-voice-assistant pi@<IP_RASPBERRY>:/home/pi/
```

## Install di Raspberry Pi

SSH ke Raspberry Pi atau buka terminal di RPi:

```bash
cd /home/pi/sips-voice-assistant
sudo apt update
sudo apt install -y portaudio19-dev python3-pip
python3 setup.py
```

Lalu jalankan test yang sama:
```bash
python3 audio_test.py
python3 tts_test.py
```

## Troubleshooting

### Mic tidak terdeteksi di Windows
- Pastikan mic sudah diaktifkan di Settings > Privacy > Microphone
- Cek di Sound Settings apakah mic terdeteksi

### Speaker tidak terdengar
- Cek volume Windows atau RPi
- Cek apakah jack audio tersambung dengan benar (RPi 4)
- Untuk RPi 5, gunakan USB Sound Card

### Edge-TTS error "No connection"
- Cek koneksi internet
- Jika internet terblokir, gunakan pyttsx3 (offline)

### pyttsx3 error di Windows
- Normal, beberapa sistem Windows tidak support pyttsx3
- Gunakan Edge-TTS sebagai gantinya

## Next Steps

Setelah audio dan TTS berfungsi:
1. Tambahkan Speech-to-Text (Whisper API atau whisper.cpp)
2. Integrasi dengan AI (OpenAI API atau Ollama lokal)
3. Tambahkan display GIF untuk ekspresi wajah tanaman
4. Hubungkan dengan Firebase RTDB untuk data sensor ESP32

---
Project SIPS - Super Intelligent Plant System
Arfalindo Nova Hidayat - SMK Leonardo Klaten
