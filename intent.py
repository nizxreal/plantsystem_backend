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
    "kering", "basah", "panas", "dingin", "harus gimana", "solusi", "bantu"
)
ACTUATOR_QUERY_WORDS = ("aktuator", "pompa")
PLANT_CONTEXT_WORDS = ("tanaman", "sensor", "suhu", "kelembapan", "ph", "pompa", "siram", "air", "kabut")
UNKNOWN_REPLY = "Aku masih belum paham maksudnya. Bisa tanyakan kondisi tanaman, nyalakan pompa, atau tips merawat tanaman."


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
        if "kering" in q or "kerin" in q or "haus" in q:
            return "Kalau tanahnya kering, siram perlahan sampai lembap, jangan sampai tergenang. Kalau mau praktis, nyalakan pompa air lewat perintah: nyalakan pompa."
        if "pupuk" in q:
            return "Untuk daun, pakai pupuk tinggi nitrogen. Untuk buah, pakai pupuk tinggi kalium dan fosfor. Pupuk organik lebih aman untuk pemula."
        if "cabai" in q:
            return "Cabai butuh sinar matahari langsung, air secukupnya, dan jangan overwatering. Daun kuning tandanya berlebih air atau kekurangan nutrisi."
        if "hama" in q or "penyakit" in q or "serang" in q:
            return "Jangan langsung semprot kimia. Pisahkan daun yang sakit, jaga sirkulasi udara, cek apakah ada ulat atau kutu, lalu pakai pestisida nabati dulu."
        return None
    return UNKNOWN_REPLY if kind == "unknown" else None
