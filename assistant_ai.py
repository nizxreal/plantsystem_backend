#!/usr/bin/env python3
"""
smile Voice Assistant - Tanpa PyAudio
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
from llm_client import GeminiRotator
from intent import route_intent, local_answer
from dotenv import load_dotenv

load_dotenv()

SAMPLE_RATE = 16000
CHANNELS = 1
DURATION = 5
VOICE_ID = os.getenv("TTS_VOICE", "id-ID-GadisNeural")
TTS_RATE = os.getenv("TTS_RATE", "+5%")
TTS_PITCH = os.getenv("TTS_PITCH", "+0Hz")


async def speak(text):
    """Generate suara dengan edge-tts dan putar via sounddevice."""
    print("[AI]:", text)
    temp_audio = "temp_response.mp3"
    
    proc = await asyncio.create_subprocess_exec(
        "edge-tts", "--text", text, "--voice", VOICE_ID,
        "--rate", TTS_RATE, "--pitch", TTS_PITCH,
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
    gemini = GeminiRotator()
    print("=" * 60)
    print("smile AI VOICE ASSISTANT")
    print("Contoh: 'status tanaman', 'nyalakan pompa', 'keluar'")
    print("=" * 60)
    
    await speak("Sistem smile siap. Ada yang bisa saya bantu?")
    
    while True:
        user_input = listen_sounddevice()
        if not user_input:
            continue
            
        intent = route_intent(user_input)

        if intent["type"] == "exit":
            await speak("Baik, sistem dinonaktifkan. Sampai jumpa!")
            break

        if intent["type"] == "actuator":
            if intent["target"] == "water":
                db.set_water_pump(intent["state"])
                await speak("Pompa air penyiraman dinyalakan." if intent["state"] else "Pompa air penyiraman dimatikan.")
            else:
                db.set_mist_pump(intent["state"])
                await speak("Pompa pengkabutan diaktifkan." if intent["state"] else "Pompa pengkabutan dimatikan.")

        elif intent["type"] == "sensor":
            await speak(describe_sensors(db.get_sensors()))

        else:
            # Chat bebas & pertanyaan spesifik -> jawaban lokal dulu, kalau tidak ada baru ke Gemini.
            answer = local_answer(intent, db)
            if answer:
                await speak(answer)
            else:
                sensors = db.get_sensors()
                sensor_context = describe_sensors(sensors)
                response = gemini.ask(user_input, sensor_context)
                if response:
                    await speak(response)
                elif gemini.has_keys:
                    await speak("Maaf, koneksi asisten sedang bermasalah. Coba lagi sebentar ya.")
                else:
                    await speak("Aku bisa ngobrol soal tanaman, sensor, tanah, dan penyiraman. Coba tanya kondisi tanaman ya.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram dihentikan.")
