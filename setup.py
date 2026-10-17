#!/usr/bin/env python3
"""
Setup & Run Script untuk SIPS Voice Assistant
Jalankan ini dulu untuk install dependencies.
"""

import subprocess
import sys
import os

def run_cmd(cmd, desc=""):
    """Jalankan command dan tampilkan hasilnya."""
    if desc:
        print(f"\n{desc}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=False)
        return result.returncode == 0
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("SIPS VOICE ASSISTANT - SETUP")
    print("="*60)
    
    # Cek Python version
    if sys.version_info < (3, 7):
        print("ERROR: Python 3.7+ diperlukan.")
        sys.exit(1)
    
    print(f"✓ Python {sys.version.split()[0]} OK")
    
    # Install dependencies
    print("\nMenginstall dependencies dari requirements.txt...")
    if not run_cmd(f"{sys.executable} -m pip install -r requirements.txt --quiet", "Install packages"):
        print("⚠️  Beberapa package gagal terinstall. Coba manual: pip install -r requirements.txt")
    else:
        print("✓ Dependencies terinstall")
    
    print("\n" + "="*60)
    print("SETUP SELESAI")
    print("="*60)
    print("\nLangkah berikutnya:")
    print("1. Test Audio:     python audio_test.py")
    print("2. Test TTS:       python tts_test.py")
    print("3. Test STT:       python stt_test.py")
    print("4. Voice Chat:     python voice_chat.py")
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    main()
