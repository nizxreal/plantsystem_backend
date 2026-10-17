#!/usr/bin/env python3
"""
Audio Test: Rekam suara dari mic, mainkan kembali ke speaker.
Guna: Cek apakah mic dan speaker terdeteksi dan berfungsi normal di PC atau RPi.
"""

import sounddevice as sd
import soundfile as sf
import numpy as np

def list_devices():
    """Tampilkan semua device audio yang tersedia."""
    print("\n" + "="*60)
    print("DAFTAR DEVICE AUDIO YANG TERSEDIA")
    print("="*60)
    devices = sd.query_devices()
    print(devices)
    print("="*60 + "\n")

def test_audio():
    """Rekam suara dari mic, mainkan kembali dari speaker."""
    DURATION = 5  # detik
    FS = 16000  # sample rate
    
    list_devices()
    
    mic_device = None
    # Auto-detect default input device (tanpa error jika index invalid)
    default_input = sd.default.device[0]
    if default_input is not None and default_input >= 0:
        try:
            dev = sd.query_devices(default_input)
            if dev['max_input_channels'] > 0:
                mic_device = default_input
                print(f"Menggunakan mic default: {dev['name']} (index {default_input})\n")
            else:
                print("Default input bukan mic. Mencari mic lain...")
        except Exception:
            print("Default input tidak valid. Mencari mic lain...")
    if mic_device is None:
        print("Mencari mic yang tersedia...")
        for i, d in enumerate(sd.query_devices()):
            if d['max_input_channels'] > 0:
                mic_device = i
                print(f"Menggunakan mic: {d['name']} (index {i})\n")
                break
    if mic_device is None:
        print("ERROR: Tidak ada mic yang terdeteksi.\n")
        return
    
    print(f"\nRekam selama {DURATION} detik... Bicara sekarang!")
    print("(Pastikan speaker tidak terlalu dekat mic, hindari feedback)")
    
    try:
        # Rekam audio
        recording = sd.rec(int(DURATION * FS), samplerate=FS, channels=1, 
                          dtype='int16', device=mic_device)
        sd.wait()
        print("Rekam selesai.")
        
        # Simpan file
        sf.write("test_recording.wav", recording, FS)
        print("File disimpan: test_recording.wav")
        
        # Mainkan balik
        print("\nMainkan balik suara tadi dari speaker...")
        sd.play(recording, FS)
        sd.wait()
        print("Playback selesai.\n")
        
        # Cek hasil
        if np.max(np.abs(recording)) < 100:
            print("⚠️  PERINGATAN: Volume rekam sangat kecil. Cek level mic atau posisi mic.")
        else:
            print("✓ Audio test OK. Mic dan speaker berfungsi normal.\n")
    
    except Exception as e:
        print(f"ERROR: {e}\n")
        print("Kemungkinan penyebab:")
        print("- Driver audio tidak terpasang atau tidak kompatibel")
        print("- Device tidak terdeteksi (cek daftar di atas)")
        print("- Mic/speaker tidak tersambung")

if __name__ == "__main__":
    test_audio()
