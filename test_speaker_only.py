#!/usr/bin/env python3
"""
Test Speaker Only: Putar file audio dari speaker.
Guna: Test speaker terpisah tanpa perlu mic.
"""

import sounddevice as sd
import soundfile as sf
import os

def test_speaker():
    """Putar file audio dari speaker."""
    print("\n" + "="*60)
    print("TEST SPEAKER ONLY")
    print("="*60)
    
    # List devices
    devices = sd.query_devices()
    print("\nDaftar output devices:")
    for i, d in enumerate(devices):
        if d['max_output_channels'] > 0:
            print(f"  [{i}] {d['name']}")
    
    # Auto-detect speaker
    speaker_device = None
    default_output = sd.default.device[1]
    if default_output is not None and default_output >= 0:
        try:
            dev = sd.query_devices(default_output)
            if dev['max_output_channels'] > 0:
                speaker_device = default_output
                print(f"\nMenggunakan speaker: {dev['name']} (index {default_output})")
        except Exception:
            pass
    
    if speaker_device is None:
        for i, d in enumerate(devices):
            if d['max_output_channels'] > 0:
                speaker_device = i
                print(f"\nMenggunakan speaker: {d['name']} (index {i})")
                break
    
    if speaker_device is None:
        print("\nERROR: Tidak ada speaker terdeteksi.")
        print("Pastikan headset colok ke jack HIJAU (output).\n")
        return
    
    # Cari file untuk diputar
    test_files = ["test_mic.wav", "test_recording.wav"]
    file_to_play = None
    
    for f in test_files:
        if os.path.exists(f):
            file_to_play = f
            break
    
    if file_to_play is None:
        print("\nTidak ada file test_mic.wav atau test_recording.wav.")
        print("Jalankan test_mic_only.py dulu untuk buat rekaman.\n")
        return
    
    print(f"\nMemutar file: {file_to_play}")
    
    try:
        data, samplerate = sf.read(file_to_play)
        sd.play(data, samplerate, device=speaker_device)
        sd.wait()
        print("\n✓ Playback selesai. Speaker berfungsi normal.")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\nERROR: {e}\n")

if __name__ == "__main__":
    test_speaker()
