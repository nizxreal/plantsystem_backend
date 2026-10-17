#!/usr/bin/env python3
"""
TTS Test: Konversi teks ke suara dan putar dari speaker.
Guna: Cek apakah speaker berfungsi dan TTS engine berjalan normal.
"""

import asyncio
import subprocess
import tempfile
import os
import sys

try:
    import sounddevice as sd
    import soundfile as sf
except ImportError:
    print("ERROR: sounddevice atau soundfile belum terinstal.")
    print("Jalankan: pip install -r requirements.txt")
    sys.exit(1)

# Teks yang akan diucapkan
TEXT_BAHASA = "Halo, ini tes suara untuk sistem SIPS. Raspberry Pi dan speaker berfungsi normal."

async def test_edge_tts():
    """Test TTS menggunakan Edge-TTS (Microsoft, kualitas tinggi, butuh internet)."""
    print("\n" + "="*60)
    print("TEST TTS: EDGE-TTS (Microsoft)")
    print("="*60)
    
    try:
        # Cek apakah edge-tts terinstal
        check = subprocess.run(['edge-tts', '--version'], capture_output=True)
        if check.returncode != 0:
            print("Edge-TTS belum terinstal. Install: pip install edge-tts")
            return False
    except FileNotFoundError:
        print("Edge-TTS belum terinstal. Install: pip install edge-tts")
        return False
    
    print("Membuat audio dari teks...")
    print(f'Teks: "{TEXT_BAHASA}"')
    
    # Buat file temporary
    temp_file = tempfile.mktemp(suffix=".mp3")
    
    # Voice ID Indonesia (pilih salah satu):
    # id-ID-ArdiNeural (pria)
    # id-ID-GadisNeural (wanita)
    voice_id = "id-ID-ArdiNeural"
    
    # Generate TTS
    cmd = ['edge-tts', '--text', TEXT_BAHASA, '--voice', voice_id, '--write-media', temp_file]
    proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    await proc.wait()
    
    if proc.returncode != 0:
        print("ERROR: Gagal generate TTS. Cek koneksi internet.")
        return False
    
    print(f"Audio tersimpan: {temp_file}")
    print("Putar dari speaker...")
    
    # Load dan putar audio
    try:
        data, samplerate = sf.read(temp_file)
        sd.play(data, samplerate)
        sd.wait()
        print("✓ TTS berhasil. Speaker berfungsi normal.\n")
        
        # Hapus file temporary
        os.remove(temp_file)
        return True
    except Exception as e:
        print(f"ERROR saat putar audio: {e}")
        return False

def test_pyttsx3():
    """Test TTS menggunakan pyttsx3 (offline, suara robot, tidak butuh internet)."""
    print("\n" + "="*60)
    print("TEST TTS: PYTTSX3 (Offline)")
    print("="*60)
    
    try:
        import pyttsx3
    except ImportError:
        print("pyttsx3 belum terinstal. Install: pip install pyttsx3")
        return False
    
    print("Membuat audio dari teks (offline)...")
    print(f'Teks: "{TEXT_BAHASA}"')
    
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)  # Kecepatan bicara
        engine.setProperty('volume', 1.0)  # Volume
        
        # Coba set voice Indonesia jika tersedia
        voices = engine.getProperty('voices')
        for voice in voices:
            if 'indonesia' in voice.name.lower() or 'id-ID' in voice.id:
                engine.setProperty('voice', voice.id)
                break
        
        engine.say(TEXT_BAHASA)
        engine.runAndWait()
        print("✓ TTS berhasil (pyttsx3). Speaker berfungsi normal.\n")
        return True
    except Exception as e:
        print(f"ERROR: {e}")
        print("pyttsx3 kadang gagal di beberapa sistem.")
        return False

async def main():
    """Jalankan semua test TTS."""
    print("\n🔊 MULAI TEST TEXT-TO-SPEECH")
    
    # Test Edge-TTS (butuh internet, kualitas tinggi)
    edge_ok = await test_edge_tts()
    
    # Test pyttsx3 (offline, kualitas standar)
    pyttsx3_ok = test_pyttsx3()
    
    print("\n" + "="*60)
    print("RINGKASAN TEST TTS")
    print("="*60)
    print(f"Edge-TTS (online):  {'✓ OK' if edge_ok else '✗ GAGAL'}")
    print(f"pyttsx3 (offline):  {'✓ OK' if pyttsx3_ok else '✗ GAGAL'}")
    print("="*60)
    
    if edge_ok or pyttsx3_ok:
        print("\n✓ Minimal 1 TTS engine berfungsi. Speaker OK.\n")
    else:
        print("\n⚠️  Tidak ada TTS engine yang berhasil. Cek speaker atau driver audio.\n")

if __name__ == "__main__":
    asyncio.run(main())
