#!/usr/bin/env python3
"""
Test Mic Only: Rekam dari mic, simpan ke file.
Guna: Test mic terpisah tanpa perlu speaker.
"""

import sounddevice as sd
import soundfile as sf
import numpy as np

DURATION = 5  # detik
FS = 16000  # sample rate

def test_mic():
    """Rekam dari mic, simpan ke file."""
    print("\n" + "="*60)
    print("TEST MIC ONLY")
    print("="*60)
    
    # List devices
    devices = sd.query_devices()
    print("\nDaftar input devices:")
    for i, d in enumerate(devices):
        if d['max_input_channels'] > 0:
            print(f"  [{i}] {d['name']}")
    
    # Auto-detect mic
    mic_device = None
    default_input = sd.default.device[0]
    if default_input is not None and default_input >= 0:
        try:
            dev = sd.query_devices(default_input)
            if dev['max_input_channels'] > 0:
                mic_device = default_input
                print(f"\nMenggunakan mic: {dev['name']} (index {default_input})")
        except Exception:
            pass
    
    if mic_device is None:
        for i, d in enumerate(devices):
            if d['max_input_channels'] > 0:
                mic_device = i
                print(f"\nMenggunakan mic: {d['name']} (index {i})")
                break
    
    if mic_device is None:
        print("\nERROR: Tidak ada mic terdeteksi.\n")
        return
    
    print(f"\nRekam selama {DURATION} detik... Bicara sekarang!")
    
    try:
        recording = sd.rec(int(DURATION * FS), samplerate=FS, channels=1, 
                          dtype='int16', device=mic_device)
        sd.wait()
        print("Rekam selesai.")
        
        # Simpan
        sf.write("test_mic.wav", recording, FS)
        print("\nFile tersimpan: test_mic.wav")
        
        # Analisis
        peak = np.max(np.abs(recording))
        print(f"Volume peak: {peak}")
        
        if peak < 100:
            print("\n⚠️  PERINGATAN: Volume sangat kecil. Cek:")
            print("   - Posisi mic dekat mulut")
            print("   - Volume mic di Windows Sound Settings")
            print("   - Headset tersambung ke jack PINK (mic input)")
        else:
            print("\n✓ Mic berfungsi normal.")
        
        print("\nUntuk dengar hasil rekaman:")
        print("1. Pindah headset ke jack HIJAU (speaker)")
        print("2. Jalankan: python test_speaker_only.py")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\nERROR: {e}\n")

if __name__ == "__main__":
    test_mic()
