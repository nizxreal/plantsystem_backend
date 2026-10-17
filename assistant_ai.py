#!/usr/bin/env python3
"""
SIPS Voice Assistant - Tanpa PyAudio
Menggunakan sounddevice untuk mic dan speaker.
"""

import os
import asyncio
import io
import wave
import numpy as np
import sounddevice as sd
import soundfile as sf
import speech_recognition as sr
from firebase_client import FirebaseRTDB, describe_sensors

SAMPLE_RATE = 16000
CHANNELS = 1
DURATION = 5
VOICE_ID = "id-ID-ArdiNeural"


async def speak(text):
    """Generate suara dengan edge-tts dan putar via sounddevice."""
    print("[AI]:", text)
    temp_audio = "temp_response.mp3"
    
    proc = await asyncio.create_subprocess_exec(
        "edge-tts", "--text", text, "--voice", VOICE_ID, 
        "--write-media", temp_audio,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL
    )
    await proc.wait()
    
    if os.path.exists(temp_audio):
        try:
            data, fs = sf.read(temp_audio)
            sd.play(data, fs)
            sd.wait()
        except Exception as e:
            print(f"(Gagal putar: {e})")
        finally:
            try:
                os.remove(temp_audio)
            except Exception:
                pass


def listen_sounddevice():
    """Rekam dari mic pakai sounddevice, kirim ke Google STT."""
    print("[Mendengarkan...]")
    try:
        recording = sd.rec(
            int(DURATION * SAMPLE_RATE), 
            samplerate=SAMPLE_RATE, 
            channels=CHANNELS, 
            dtype='int16'
        )
        sd.wait()
        
        volume_level = np.max(np.abs(recording))
        if volume_level < 300:
            print("(Suara terlalu pelan)")
            return None
        
        wav_io = io.BytesIO()
        with wave.open(wav_io, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(recording.tobytes())
        wav_io.seek(0)
        
        r = sr.Recognizer()
        with sr.AudioFile(wav_io) as source:
            audio_data = r.record(source)
            text = r.recognize_google(audio_data, language="id-ID")
            print("[User]:", text)
            return text.lower()
            
    except sr.UnknownValueError:
        print("(Tidak terdengar jelas)")
        return None
    except sr.RequestError as e:
        print(f"(Gagal koneksi STT: {e})")
        return None
    except Exception as e:
        print(f"(Error: {e})")
        return None


async def main():
    db = FirebaseRTDB()
    print("=" * 60)
    print("SIPS AI VOICE ASSISTANT")
    print("Contoh: 'status tanaman', 'nyalakan pompa', 'keluar'")
    print("=" * 60)
    
    await speak("Sistem SIPS siap. Ada yang bisa saya bantu?")
    
    while True:
        user_input = listen_sounddevice()
        if not user_input:
            continue
            
        if "keluar" in user_input or "berhenti" in user_input or "selesai" in user_input:
            await speak("Baik, sistem dinonaktifkan. Sampai jumpa!")
            break
            
        if "status" in user_input or "kondisi" in user_input or "tanaman" in user_input:
            sensors = db.get_sensors()
            laporan = describe_sensors(sensors)
            await speak(laporan)
            
        elif "nyalakan pompa" in user_input or "hidupkan pompa" in user_input or "siram" in user_input:
            db.set_water_pump(True)
            await speak("Pompa air penyiraman dinyalakan.")
            
        elif "matikan pompa" in user_input or "hentikan pompa" in user_input:
            db.set_water_pump(False)
            await speak("Pompa air dimatikan.")
            
        elif "kabut" in user_input or "mist" in user_input:
            if "nyala" in user_input or "hidup" in user_input:
                db.set_mist_pump(True)
                await speak("Pompa pengkabutan diaktifkan.")
            else:
                db.set_mist_pump(False)
                await speak("Pompa pengkabutan dimatikan.")
                
        else:
            await speak("Perintah belum dikenali. Coba tanyakan status tanaman atau perintahkan pompa.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram dihentikan.")
