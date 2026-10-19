#!/usr/bin/env python3
"""
Firebase RTDB Client untuk smile Voice Assistant.

Struktur database:
  /smile/sensors/: temperature, humidity, soil_moisture, soil_ph
  /smile/actuators/: water_pump, mist_pump (boolean)

Pakai REST API langsung (tanpa firebase-admin SDK) supaya ringan di Raspberry Pi.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

DEFAULT_URL = "https://linoplantsys-default-rtdb.asia-southeast1.firebasedatabase.app"

SENSORS_PATH = "smile/sensors"
ACTUATORS_PATH = "smile/actuators"
CMD_PATH = "smile/commands"

TIMEOUT = 10


class FirebaseError(Exception):
    """Kegagalan akses ke Firebase RTDB."""


class FirebaseRTDB:
    """Client REST sederhana untuk Firebase Realtime Database."""

    def __init__(self, base_url=None, timeout=TIMEOUT):
        self.base_url = (base_url or os.getenv("FIREBASE_URL") or DEFAULT_URL).rstrip("/")
        self.timeout = timeout

    # ---------- helper ----------
    def _url(self, path):
        return f"{self.base_url}/{path.strip('/')}.json"

    def get(self, path):
        """Baca data dari path. Return dict atau None."""
        try:
            r = requests.get(self._url(path), timeout=self.timeout)
            if r.status_code != 200:
                raise FirebaseError(f"GET {path} -> HTTP {r.status_code}: {r.text[:200]}")
            return r.json()
        except requests.RequestException as e:
            raise FirebaseError(f"Gagal koneksi ke Firebase: {e}")

    def patch(self, path, data):
        """Update sebagian data pada path."""
        try:
            r = requests.patch(self._url(path), json=data, timeout=self.timeout)
            if r.status_code != 200:
                raise FirebaseError(f"PATCH {path} -> HTTP {r.status_code}: {r.text[:200]}")
            return r.json()
        except requests.RequestException as e:
            raise FirebaseError(f"Gagal koneksi ke Firebase: {e}")

    # ---------- domain helpers ----------
    def get_sensors(self):
        """Baca data sensor ESP32."""
        return self.get(SENSORS_PATH) or {}

    def get_actuators(self):
        """Baca status aktuator (pompa)."""
        return self.get(ACTUATORS_PATH) or {}

    def set_water_pump(self, state):
        return self.patch(ACTUATORS_PATH, {"water_pump": bool(state)})

    def set_mist_pump(self, state):
        return self.patch(ACTUATORS_PATH, {"mist_pump": bool(state)})

    def log_command(self, text, action, success=True):
        """Simpan riwayat perintah ke Firebase (opsional, gagal tidak fatal)."""
        import datetime
        entry = {
            "text": text,
            "action": action,
            "success": bool(success),
            "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
        }
        try:
            self.patch(f"{CMD_PATH}/{entry['timestamp'].replace(':', '-')}", entry)
        except FirebaseError:
            pass


# ---------- format sensor ke kalimat bahasa Indonesia ----------

SENSOR_LABELS = {
    "temperature": ("suhu udara", "derajat Celsius"),
    "humidity": ("kelembapan udara", "persen"),
    "soil_moisture": ("kelembapan tanah", "persen"),
    "soil_ph": ("pH tanah", ""),
}

RANGES = {
    "temperature": (20, 30),
    "humidity": (50, 80),
    "soil_moisture": (40, 70),
    "soil_ph": (6.0, 7.0),
}


def describe_sensors(sensors):
    """Ubah dict sensor jadi kalimat natural berisi nilai dan penilaian kondisi."""
    if not sensors:
        return "Belum ada data sensor dari ESP32. Pastikan ESP32 sudah terhubung."

    parts = []
    for key, (label, unit) in SENSOR_LABELS.items():
        val = sensors.get(key)
        if val is None:
            continue
        lo, hi = RANGES[key]
        if key == "soil_ph":
            kondisi = "asam" if val < lo else ("basa" if val > hi else "ideal")
        else:
            kondisi = "terlalu rendah" if val < lo else ("terlalu tinggi" if val > hi else "normal")

        angka = f"{val:g}" if isinstance(val, (int, float)) else str(val)
        parts.append(f"{label} {angka}{' ' + unit if unit else ''} ({kondisi})")

    if not parts:
        return "Data sensor ada tapi tidak lengkap."

    return "Kondisi tanaman sekarang: " + ", ".join(parts) + "."