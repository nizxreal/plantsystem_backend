"""Intent router lokal untuk smile Voice Assistant."""

STOP_WORDS = ("keluar", "berhenti", "selesai", "stop")
GREETING_WORDS = ("halo", "hai", "hello", "hy", "selamat", "pagi", "siang", "sore", "malam", "apa kabar", "kabar")
SENSOR_WORDS = ("status tanaman", "kondisi tanaman", "suhu", "kelembapan", "kelembaban", "ph", "sensor", "data sensor")
WATER_PUMP_WORDS = ("pompa air", "pompa penyiraman", "siram", "penyiraman")
MIST_PUMP_WORDS = ("pompa kabut", "pompa pengkabutan", "mist")
ON_WORDS = ("nyalakan", "hidupkan", "aktifkan", "mulai", "sirami", "siram")
OFF_WORDS = ("matikan", "hentikan", "stop", "nonaktifkan")
CHAT_WORDS = (
    "tips", "cara", "kenapa", "mengapa", "sebab", "pupuk", "hama", "penyakit",
    "cabai", "tomat", "selada", "kangkung", "bayam", "obat", "tanya", "chat",
    "ngobrol", "marah", "sedih", "nangis", "senang", "mood", "ekspresi",
    "kering", "basah", "panas", "dingin", "harus gimana", "solusi", "bantu",
    "kampus", "panitia", "tingkat kampus", "oot", "nyeleneh", "random", "lucu",
    "masa depan", "belajar", "autostart", "systemd", "firebase", "debug", "bug",
    "sensor saja", "data sensor", "kerusakan", "tidak jalan", "list perintah",
    "mode tersembunyi", "racun", "bercanda", "tipuan", "hobi", "kontes",
    # Kata tanya & kata kunci teknis / penguji
    "apa", "siapa", "bagaimana", "gimana", "berapa", "apakah",
    "kelebihan", "keunggulan", "banding", "smart farming",
    "dual controller", "esp32", "raspberry", "rpi",
    "terputus", "koneksi", "offline", "tanpa internet", "internet",
    "protokol", "komunikasi", "latensi", "latency", "kecepatan",
    "fungsi", "tujuan", "alat", "komponen", "otomatis",
    "daya", "listrik", "baterai", "catu", "padam", "mati lampu",
    "beda", "perbedaan", "robot", "manusia", "kopi", "boba", "curhat",
    "galau", "cemberut", "gebetan"
)
ACTUATOR_QUERY_WORDS = ("aktuator", "pompa")
PLANT_CONTEXT_WORDS = ("tanaman", "sensor", "suhu", "kelembapan", "ph", "pompa", "siram", "air", "kabut")
UNKNOWN_REPLY = "Bisa ulangi pertanyaannya?"


def route_intent(text: str) -> dict:
    t = (text or "").lower().strip()
    if any(w in t for w in STOP_WORDS):
        return {"type": "exit"}

    # Prioritas: sapaan/obrolan umum tanpa konteks tanaman -> ke Gemini
    if any(w in t for w in GREETING_WORDS):
        if not any(w in t for w in PLANT_CONTEXT_WORDS):
            return {"type": "chat", "query": t}

    if any(w in t for w in SENSOR_WORDS):
        return {"type": "sensor"}

    for pump, words in (("water", WATER_PUMP_WORDS), ("mist", MIST_PUMP_WORDS)):
        if any(w in t for w in words):
            state = True if any(w in t for w in ON_WORDS) else False if any(w in t for w in OFF_WORDS) else None
            if state is not None:
                return {"type": "actuator", "target": pump, "state": state}
            if any(w in t for w in ACTUATOR_QUERY_WORDS):
                return {"type": "actuator_status", "target": pump}

    if any(w in t for w in CHAT_WORDS):
        return {"type": "chat", "query": t}

    return {"type": "unknown"}


def local_answer(intent: dict, db) -> str | None:
    kind = intent["type"]
    if kind == "sensor":
        from firebase_client import describe_sensors
        return describe_sensors(db.get_sensors())
    if kind == "actuator_status":
        value = db.get_actuators().get(f"{intent['target']}_pump")
        state = "aktif" if value else "mati"
        return f"Pompa {intent['target']} sekarang {state}."
    if kind == "chat":
        q = intent["query"]
        # Perawatan dasar & kondisi tanaman
        if "kering" in q or "kerin" in q or "haus" in q:
            return "Kalau tanahnya kering, siram perlahan sampai lembap, jangan sampai tergenang. Kalau mau praktis, nyalakan pompa air lewat perintah: nyalakan pompa."
        if "pupuk" in q:
            return "Untuk daun, pakai pupuk tinggi nitrogen. Untuk buah, pakai pupuk tinggi kalium dan fosfor. Pupuk organik lebih aman untuk pemula."
        if "cabai" in q:
            return "Cabai butuh sinar matahari langsung, air secukupnya, dan jangan overwatering. Daun kuning tandanya berlebih air atau kekurangan nutrisi."
        if "hama" in q or "penyakit" in q or "serang" in q:
            return "Jangan langsung semprot kimia. Pisahkan daun yang sakit, jaga sirkulasi udara, cek apakah ada ulat atau kutu, lalu pakai pestisida nabati dulu."

        # Pertanyaan Teknis / Penguji Tingkat Kampus
        if "kelebihan" in q or "banding" in q or "smart farming" in q:
            return "Kelebihan sistem ini dibanding smart farming biasa adalah integrasi voice assistant interaktif dan display ekspresi wajah lokal via Raspberry Pi yang membuat interaksi terasa hidup, bukan sekadar angka di dashboard."
        if "dual controller" in q or ("kenapa" in q and "esp32" in q and ("rpi" in q or "raspberry" in q)):
            return "ESP32 fokus membaca sensor dan aktuator secara stabil real-time. Sedangkan Raspberry Pi menangani komputasi berat seperti GUI ekspresi, pengenalan suara, dan pemrosesan AI."
        if "terputus" in q or "koneksi" in q or "offline" in q or "tanpa internet" in q:
            return "Jika koneksi internet putus, ESP32 tetap menjalankan logika penyiraman lokal otomatis, dan voice assistant tetap menjawab pertanyaan lewat basis data lokal tanpa cloud."
        if "protokol" in q or "komunikasi" in q:
            return "Sistem menggunakan Firebase Realtime Database lewat koneksi WebSockets dan REST API untuk sinkronisasi data sensor dan status aktuator secara instan."
        if "latensi" in q or "latency" in q or "kecepatan" in q or "berapa" in q:
            return "Latensi respon sistem sekitar satu sampai dua detik untuk perintah suara lokal, dan kurang dari satu detik bila dioperasikan lewat layar sentuh."
        if "sensor apa saja" in q or ("daftar" in q and "sensor" in q):
            return "Sistem menggunakan sensor kelembapan tanah, suhu dan kelembapan udara DHT, serta sensor pH tanah untuk memantau kelayakan media tanam secara komprehensif."

        # Pertanyaan Teknis Dasar / Tingkat SMA-SMK
        if "fungsi utama" in q or "tujuan alat" in q:
            return "Fungsi utama alat ini adalah membantu merawat tanaman secara otomatis dengan membaca sensor kondisi lingkungan, lalu menyiram otomatis atau lewat kontrol suara dan layar sentuh."
        if "kenapa" in q and "otomatis" in q:
            return "Penyiraman otomatis mencegah tanaman layu karena lupa disiram, sekaligus menghindari busuk akar akibat kelebihan air."
        if "sumber listrik" in q or "daya" in q or "catu daya" in q:
            return "Alat ini menggunakan catu daya DC 5 Volt untuk Raspberry Pi dan ESP32, serta power supply terpisah yang aman untuk aktuator pompa air."
        if "komponen apa" in q or "daftar komponen" in q or "alat apa saja" in q:
            return "Komponen utamanya adalah ESP32, Raspberry Pi Model B, LCD sentuh Waveshare 7 inci, mikrofon USB, speaker, modul relay, dan pompa mini DC."
        if "beda pompa" in q or ("air" in q and "kabut" in q):
            return "Pompa air mengalirkan air ke akar saat tanah kering, sedangkan pompa kabut menyemprotkan uap air ke udara saat suhu ruangan panas atau udara kering."
        if "listrik padam" in q or "mati lampu" in q:
            return "Jika listrik padam sistem mati sementara, tetapi begitu daya kembali, layanan autostart akan langsung menyalakan display dan asisten secara otomatis."

        # Pertanyaan OOT & Nyeleneh
        if "robot atau manusia" in q or "siapa kamu" in q:
            return "Aku asisten virtual smile. Bukan manusia, tapi aku peduli sama tanamanmu lebih dari mantanmu."
        if "kopi" in q or "boba" in q or "teh" in q:
            return "Jangan siram pakai kopi atau boba, tanaman butuh air bersih. Nanti tanamannya insomnia dan dikerubungi semut."
        if "curhat" in q or "galau" in q:
            return "Boleh banget curhat. Tanaman adalah pendengar setia yang aman karena mereka nggak bakal membocorkan rahasiamu."
        if "cemberut" in q or "marah" in q or "nangis" in q or "sedih" in q:
            return "Ekspresiku mengikuti kondisi tanaman. Kalau tanahnya kering atau kepanasan, aku ikut sedih dan butuh bantuanmu."
        if "gebetan" in q:
            return "Pompa kabut bisa mendinginkan udara panas, tapi kalau menghadapi gebetan yang dingin, kamu butuh perhatian ekstra bukan air."

        return None
    return UNKNOWN_REPLY if kind == "unknown" else None
