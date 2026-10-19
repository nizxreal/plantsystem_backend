#!/usr/bin/env python3
"""
smile Mood & Controller Display
Tampilan ekspresi wajah + tombol touchscreen di LCD Waveshare 7 inch.
"""

import os
import tkinter as tk
from tkinter import font
from firebase_client import FirebaseRTDB
from dotenv import load_dotenv

load_dotenv()

class smileDisplay:
    def __init__(self, root):
        self.root = root
        self.root.title("smile Plant Display")
        self.root.attributes("-fullscreen", True)
        self.root.configure(bg="#121212")

        self.db = FirebaseRTDB()

        # Binding exit key (tekan ESC untuk keluar)
        self.root.bind("<Escape>", lambda e: self.root.destroy())

        # Frame Utama
        self.main_frame = tk.Frame(root, bg="#121212")
        self.main_frame.pack(expand=True, fill="both", padx=20, pady=20)

        # Header Title
        self.title_label = tk.Label(
            self.main_frame, text="smile - PLANT MONITOR",
            font=("Arial", 22, "bold"), fg="#81C784", bg="#121212"
        )
        self.title_label.pack(pady=10)

        # Mood Face Emoji
        self.face_label = tk.Label(
            self.main_frame, text="😊",
            font=("Segoe UI Emoji", 110), fg="#FFFFFF", bg="#121212"
        )
        self.face_label.pack(pady=5)

        # Status Teks
        self.status_label = tk.Label(
            self.main_frame, text="Kondisi: Normal",
            font=("Arial", 18, "bold"), fg="#4CAF50", bg="#121212"
        )
        self.status_label.pack(pady=5)

        # Sensor Baris Info
        self.sensor_label = tk.Label(
            self.main_frame,
            text="Suhu: --°C | Kelembaban: --% | Tanah: --% | pH: --",
            font=("Arial", 14), fg="#E0E0E0", bg="#121212"
        )
        self.sensor_label.pack(pady=10)

        # Frame Tombol Touchscreen Interaktif
        self.btn_frame = tk.Frame(self.main_frame, bg="#121212")
        self.btn_frame.pack(pady=15)

        self.btn_water = tk.Button(
            self.btn_frame, text="Siram Air (Pompa)",
            font=("Arial", 14, "bold"), bg="#1976D2", fg="white",
            padx=20, pady=10, relief="raised", bd=3,
            command=self.toggle_water
        )
        self.btn_water.grid(row=0, column=0, padx=15)

        self.btn_mist = tk.Button(
            self.btn_frame, text="Semprot Mist",
            font=("Arial", 14, "bold"), bg="#00897B", fg="white",
            padx=20, pady=10, relief="raised", bd=3,
            command=self.toggle_mist
        )
        self.btn_mist.grid(row=0, column=1, padx=15)

        self.water_state = False
        self.mist_state = False

        # Loop polling Firebase setiap 3 detik
        self.update_sensors()

    def update_sensors(self):
        try:
            sensors = self.db.get_sensors() or {}
            temp = float(sensors.get("temperature", 0))
            hum = float(sensors.get("humidity", 0))
            soil = float(sensors.get("soil_moisture", 0))
            ph = float(sensors.get("soil_ph", 0))

            # Update teks sensor
            self.sensor_label.config(
                text=f"Suhu: {temp:.1f}°C | Hum: {hum:.1f}% | Tanah: {soil:.1f}% | pH: {ph:.1f}"
            )

            # Hitung skor kesehatan (0 - 100)
            score = 0
            if 20 <= temp <= 32: score += 25
            if 50 <= hum <= 85: score += 25
            if soil >= 40: score += 25
            if 5.5 <= ph <= 7.5: score += 25

            # Tentukan ekspresi
            if score >= 75:
                self.face_label.config(text="😊")
                self.status_label.config(text="Tanaman Bahagia & Sehat!", fg="#4CAF50")
            elif score >= 50:
                self.face_label.config(text="😐")
                self.status_label.config(text="Kondisi Sedang Perlu Perhatian", fg="#FFB300")
            elif score >= 25:
                self.face_label.config(text="😢")
                self.status_label.config(text="Tanaman Haus / Stres!", fg="#FB8C00")
            else:
                self.face_label.config(text="😡")
                self.status_label.config(text="Kondisi Kritis! Segera Cek Tanaman", fg="#E53935")

        except Exception as e:
            self.status_label.config(text=f"Gagal baca data: {e}", fg="#E53935")

        # Ulangi setiap 3000ms
        self.root.after(3000, self.update_sensors)

    def toggle_water(self):
        self.water_state = not self.water_state
        try:
            self.db.set_water_pump(self.water_state)
            color = "#D32F2F" if self.water_state else "#1976D2"
            txt = "Matikan Air" if self.water_state else "Siram Air (Pompa)"
            self.btn_water.config(bg=color, text=txt)
        except Exception as e:
            print("Gagal ubah pompa air:", e)

    def toggle_mist(self):
        self.mist_state = not self.mist_state
        try:
            self.db.set_mist_pump(self.mist_state)
            color = "#D32F2F" if self.mist_state else "#00897B"
            txt = "Matikan Mist" if self.mist_state else "Semprot Mist"
            self.btn_mist.config(bg=color, text=txt)
        except Exception as e:
            print("Gagal ubah mist:", e)

if __name__ == "__main__":
    root = tk.Tk()
    app = smileDisplay(root)
    root.mainloop()
