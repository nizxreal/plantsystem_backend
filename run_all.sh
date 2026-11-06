#!/bin/bash
# Script untuk menjalankan display dan assistant secara bersamaan
# Tekan Ctrl+C untuk mematikan keduanya sekaligus.

cd /home/pi/Desktop/plantsystem_backend

# Tunggu display server :0 siap (maksimal 30 detik)
echo "Menunggu display server :0..."
for i in {1..30}; do
    if [ -S /tmp/.X11-unix/X0 ]; then
        echo "Display server ditemukan."
        break
    fi
    sleep 1
done

export DISPLAY=:0
export XDG_RUNTIME_DIR=/run/user/$(id -u)

# Kill semua proses python lama sebelum start ulang
echo "Membersihkan proses python lama..."
pkill -9 -f 'python3 display_ekspresi_pygame' 2>/dev/null
pkill -9 -f 'python3 assistant_ai' 2>/dev/null
sleep 2

echo "Menjalankan Display Ekspresi Pygame..."
/usr/bin/python3 display_ekspresi_pygame.py > /tmp/display.log 2>&1 &
DISPLAY_PID=$!

# Beri jeda agar window/layar display muncul duluan
sleep 5

# Verifikasi display masih hidup
if kill -0 $DISPLAY_PID 2>/dev/null; then
    echo "Display berjalan (PID $DISPLAY_PID)"
else
    echo "Display gagal start, cek /tmp/display.log"
fi

echo "Menjalankan Voice Assistant..."
# Voice assistant pakai virtualenv jika ada, fallback ke system python
if [ -f .venv/bin/python3 ]; then
    .venv/bin/python3 assistant_ai.py > /tmp/assistant.log 2>&1 &
else
    /usr/bin/python3 assistant_ai.py > /tmp/assistant.log 2>&1 &
fi
ASSISTANT_PID=$!

# Trap Ctrl+C (SIGINT) dan matikan keduanya
trap "echo 'Mematikan sistem...'; kill $DISPLAY_PID $ASSISTANT_PID 2>/dev/null; exit 0" SIGINT SIGTERM

# Pantau proses display: jika display dimatikan/logout, matikan assistant dan kunci sistem agar tidak restart
while true; do
    if ! kill -0 $DISPLAY_PID 2>/dev/null; then
        echo "Logout terdeteksi. Menghentikan assistant dan menahan sistem..."
        kill -9 $ASSISTANT_PID 2>/dev/null
        pkill -9 -f 'assistant_ai' 2>/dev/null
        # Kunci script di sini agar systemd tetap menganggap running (tidak trigger Restart=always)
        while true; do sleep 3600; done
    fi
    sleep 1
done
