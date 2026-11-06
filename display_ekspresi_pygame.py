#!/usr/bin/env python3
import sys, time, math, random, os, signal, threading, subprocess, pygame
from firebase_client import FirebaseRTDB

WIDTH, HEIGHT, FPS = 1024, 600, 30
BG_COLOR, PANEL_COLOR, TEXT_WHITE = (255, 255, 255), (242, 244, 247), (35, 38, 42)

MOOD_COLORS = {
    'happy':    {'eye': (30, 180, 80),  'status': 'Sesuai Batas Normal (Optimal)',          'status_color': (30, 160, 60),  'label': '😊 Normal'},
    'thirsty':  {'eye': (30, 130, 230), 'status': 'Menyimpang (Ditangani Otomatis)',        'status_color': (30, 120, 210),  'label': '😢 Menyimpang'},
    'critical': {'eye': (220, 40, 50),  'status': 'Kritis (Butuh Tindakan Manusia)',         'status_color': (200, 30, 30),  'label': '😠 Kritis'},
}

class SmoothVal:
    def __init__(self, val):
        self.current = self.target = float(val)
    def update(self, speed=0.15):
        self.current += (self.target - self.current) * speed
        return self.current

class AnimatedFace:
    def __init__(self, cx, cy):
        self.cx, self.cy = cx, cy
        self.mood = self.target_mood = 'happy'
        self.eye_w, self.eye_h = SmoothVal(95), SmoothVal(120)
        self.eye_spacing, self.eye_roundness = SmoothVal(130), SmoothVal(40)
        self.eyebrow_angle, self.eyebrow_offset_y = SmoothVal(0), SmoothVal(0)
        self.mouth_curve, self.mouth_open = SmoothVal(1.0), SmoothVal(0.0)
        self.blush_alpha = SmoothVal(180)
        c = MOOD_COLORS['happy']['eye']
        self.color_r, self.color_g, self.color_b = SmoothVal(c[0]), SmoothVal(c[1]), SmoothVal(c[2])
        self.gaze_x, self.gaze_y = SmoothVal(0), SmoothVal(0)
        self.next_gaze_time = time.time() + 2.0
        self.blink_val, self.is_blinking, self.blink_timer = 1.0, False, 0.0
        self.next_blink_time = time.time() + random.uniform(2.5, 4.5)
        self.breath_phase = 0.0
        self.reaction_timer = 0.0
        self.is_reacting = False
        self.is_talking = False
        self.talk_phase = 0.0
        self.talk_strength = 0.0

    def apply_mood_targets(self, mood):
        if mood not in MOOD_COLORS: return
        c = MOOD_COLORS[mood]['eye']
        self.color_r.target, self.color_g.target, self.color_b.target = c
        if mood == 'happy':
            self.eye_w.target, self.eye_h.target, self.eye_roundness.target = 100, 120, 45
            self.eyebrow_angle.target, self.eyebrow_offset_y.target = 5, 0
            self.mouth_curve.target, self.mouth_open.target, self.blush_alpha.target = 1.0, 0.2, 200
        elif mood == 'neutral':
            self.eye_w.target, self.eye_h.target, self.eye_roundness.target = 90, 110, 35
            self.eyebrow_angle.target, self.eyebrow_offset_y.target = 0, 0
            self.mouth_curve.target, self.mouth_open.target, self.blush_alpha.target = 0.1, 0.0, 60
        elif mood == 'thirsty':
            self.eye_w.target, self.eye_h.target, self.eye_roundness.target = 95, 85, 25
            self.eyebrow_angle.target, self.eyebrow_offset_y.target = -12, 6
            self.mouth_curve.target, self.mouth_open.target, self.blush_alpha.target = -0.5, 0.1, 20
        elif mood == 'critical':
            self.eye_w.target, self.eye_h.target, self.eye_roundness.target = 105, 70, 20
            self.eyebrow_angle.target, self.eyebrow_offset_y.target = 22, 14
            self.mouth_curve.target, self.mouth_open.target, self.blush_alpha.target = -0.9, 0.3, 0

    def set_mood(self, mood):
        self.target_mood = mood
        if not self.is_reacting:
            self.mood = mood
            self.apply_mood_targets(mood)

    def react(self, r_type='pet'):
        self.is_reacting, self.reaction_timer = True, 1.8
        if r_type == 'pet':
            self.eye_h.target, self.eye_roundness.target, self.eyebrow_angle.target = 45, 15, 8
            self.mouth_curve.target, self.blush_alpha.target, self.gaze_y.target = 1.2, 240, -10
            c = MOOD_COLORS['happy']['eye']
            self.color_r.target, self.color_g.target, self.color_b.target = c
        else:
            self.eye_w.target, self.eye_h.target, self.eye_roundness.target = 125, 125, 60
            self.eyebrow_angle.target, self.mouth_open.target, self.mouth_curve.target = -15, 0.75, 0.0
            self.blink_val = 1.0

    def update(self, dt):
        now = time.time()
        if self.is_reacting:
            self.reaction_timer -= dt
            if self.reaction_timer <= 0:
                self.is_reacting = False
                self.mood = self.target_mood
                self.apply_mood_targets(self.mood)
        for v in [self.eye_w, self.eye_h, self.eye_spacing, self.eye_roundness,
                  self.eyebrow_angle, self.eyebrow_offset_y, self.mouth_curve,
                  self.mouth_open, self.blush_alpha, self.color_r, self.color_g,
                  self.color_b, self.gaze_x, self.gaze_y]:
            v.update()
        self.breath_phase += dt * 2.2
        bob_y = math.sin(self.breath_phase) * 5.0
        if not self.is_reacting and now > self.next_gaze_time:
            self.gaze_x.target = random.choice([-22, -10, 0, 0, 10, 22])
            self.gaze_y.target = random.choice([-10, 0, 0, 8])
            self.next_gaze_time = now + random.uniform(1.8, 4.0)
        if not self.is_blinking and now > self.next_blink_time:
            self.is_blinking, self.blink_timer = True, 0.0
        if self.is_blinking:
            self.blink_timer += dt * 10.0
            if self.blink_timer < math.pi:
                self.blink_val = max(0.05, 1.0 - math.sin(self.blink_timer))
            else:
                self.blink_val = 1.0
                self.is_blinking = False
                self.next_blink_time = now + random.uniform(2.5, 5.5)
        if self.is_talking:
            self.talk_phase += dt * 15.0
            self.talk_strength = (math.sin(self.talk_phase) + 1.0) / 2.0
        else:
            self.talk_strength = 0.0
        return bob_y

    def draw(self, surface, bob_y):
        eye_col = (int(self.color_r.current), int(self.color_g.current), int(self.color_b.current))
        glow_col = (max(0, eye_col[0]//4), max(0, eye_col[1]//4), max(0, eye_col[2]//4))
        shake_x = random.randint(-1, 1) if (self.mood == 'critical' and not self.is_reacting) else 0
        base_y = self.cy + bob_y
        spacing, gx, gy = self.eye_spacing.current, self.gaze_x.current, self.gaze_y.current
        cur_h = max(4.0, self.eye_h.current * self.blink_val)
        cur_w = self.eye_w.current
        rad = int(min(self.eye_roundness.current, cur_h/2, cur_w/2))
        for side in (-1, 1):
            ex = self.cx + (side * spacing) + gx + shake_x
            ey = base_y - 20 + gy
            pygame.draw.rect(surface, glow_col,
                (ex - cur_w/2 - 6, ey - cur_h/2 - 6, cur_w + 12, cur_h + 12), border_radius=rad + 4)
            pygame.draw.rect(surface, eye_col,
                (ex - cur_w/2, ey - cur_h/2, cur_w, cur_h), border_radius=rad)
            if self.blink_val > 0.4:
                pygame.draw.circle(surface, (255, 255, 255),
                    (int(ex - side*15), int(ey - cur_h*0.2)), max(2, int(cur_w * 0.15)))
            angle = self.eyebrow_angle.current * side
            brow_y = ey - (cur_h/2) - 22 + self.eyebrow_offset_y.current
            rad_ang = math.radians(angle)
            half_len = cur_w * 0.55
            dx, dy = math.cos(rad_ang) * half_len, math.sin(rad_ang) * half_len
            pygame.draw.line(surface, eye_col,
                (int(ex - dx), int(brow_y - dy)), (int(ex + dx), int(brow_y + dy)), 8)
        blush_a = int(self.blush_alpha.current)
        if blush_a > 10:
            blush_surf = pygame.Surface((70, 30), pygame.SRCALPHA)
            pygame.draw.ellipse(blush_surf, (255, 105, 135, blush_a), (0, 0, 70, 30))
            for side in (-1, 1):
                surface.blit(blush_surf,
                    (int(self.cx + (side * (spacing + 35)) - 35) + shake_x, int(base_y + 40 - 15)))
        mouth_y, mw = base_y + 55, 70
        eff_open = max(self.mouth_open.current, self.talk_strength * 0.6)
        ctrl_y = int(mouth_y + (self.mouth_curve.current * 28) + (eff_open * 35))
        mouth_pts = []
        p_l = (int(self.cx - mw/2 + shake_x), int(mouth_y))
        p_r = (int(self.cx + mw/2 + shake_x), int(mouth_y))
        for i in range(21):
            t = i / 20.0
            bx = (1 - t)**2 * p_l[0] + 2 * (1 - t) * t * (self.cx + shake_x) + t**2 * p_r[0]
            by = (1 - t)**2 * p_l[1] + 2 * (1 - t) * t * ctrl_y + t**2 * p_r[1]
            mouth_pts.append((int(bx), int(by)))
        pygame.draw.lines(surface, eye_col, False, mouth_pts, 8)

class TouchButton:
    def __init__(self, rect, text, b_col, a_col, icon=''):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.icon = icon
        self.b_col = b_col
        self.a_col = a_col
        self.is_active = False
        self.pulse = 0.0

    def handle_touch(self, pos):
        return self.rect.collidepoint(pos)

    def draw(self, surface, font, dt):
        if self.is_active:
            self.pulse += dt * 4.0
            col = tuple(int(c * (0.7 + 0.3 * (math.sin(self.pulse)+1)/2)) for c in self.a_col)
            pygame.draw.rect(surface, col, self.rect, border_radius=14)
            label = f'{self.icon} MATIKAN' if self.icon else 'MATIKAN'
        else:
            pygame.draw.rect(surface, self.b_col, self.rect, border_radius=14)
            label = self.text
        pygame.draw.rect(surface, (255, 255, 255), self.rect, 2, border_radius=14)
        txt = font.render(label, True, (255, 255, 255))
        surface.blit(txt, txt.get_rect(center=self.rect.center))

class FirebaseSync:
    def __init__(self):
        self.db = FirebaseRTDB()
        self.lock = threading.Lock()
        self.sensors = {'t': 0, 'h': 0, 'sm': 0, 'ph': 0}
        self.st_txt = 'Menghubungkan...'
        self.st_col = (140, 148, 160)
        self.mood = 'neutral'
        self.water_pump = False
        self.mist_pump = False
        self.master = True
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        while self.running:
            try:
                s = self.db.get_sensors() or {}
                air = s.get('air', {})
                soil = s.get('soil', {})
                with self.lock:
                    self.sensors = {
                        't': float(air.get('temperature', s.get('temperature', 0))),
                        'h': float(air.get('humidity', s.get('humidity', 0))),
                        'sm': float(soil.get('moisture', s.get('soil_moisture', 0))),
                        'ph': float(soil.get('ph', s.get('soil_ph', 0)))
                    }
                    score = ((25 if 20 <= self.sensors['t'] <= 32 else 0) + (25 if 50 <= self.sensors['h'] <= 85 else 0) +
                             (25 if self.sensors['sm'] >= 40 else 0) + (25 if 5.5 <= self.sensors['ph'] <= 7.5 else 0))
                    # Mapping baru: Happy >= 75, Thirsty >= 40, Critical < 40
                    self.mood = 'happy' if score >= 75 else 'thirsty' if score >= 40 else 'critical'
                    self.st_txt = MOOD_COLORS[self.mood]['status']
                    self.st_col = MOOD_COLORS[self.mood]['status_color']
                
                act = self.db.get_actuators() or {}
                self.water_pump = bool(act.get('water_pump', False))
                self.mist_pump = bool(act.get('mist_pump', False))
                self.master = bool(self.db.get_master())
            except Exception:
                pass
            time.sleep(2.5)

    def set_water_pump(self, state):
        threading.Thread(target=lambda: self.db.set_water_pump(state), daemon=True).start()

    def set_mist_pump(self, state):
        threading.Thread(target=lambda: self.db.set_mist_pump(state), daemon=True).start()

    def set_master(self, state):
        threading.Thread(target=lambda: self.db.set_master(state), daemon=True).start()

    def snapshot(self):
        with self.lock:
            return self.sensors, self.st_txt, self.st_col, self.mood, self.water_pump, self.mist_pump, self.master

def get_recent_logs(max_lines=14):
    log_path = '/tmp/assistant.log'
    if not os.path.exists(log_path):
        return ['(Belum ada file log /tmp/assistant.log)']
    try:
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        non_empty = [line.strip() for line in lines if line.strip()]
        return non_empty[-max_lines:] if non_empty else ['(Log masih kosong)']
    except Exception as e:
        return [f'(Error baca log: {e})']

def main():
    os.environ['SDL_AUDIODRIVER'] = 'dummy'
    pygame.display.init()
    pygame.font.init()
    try: screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
    except: screen = pygame.display.set_mode((WIDTH, HEIGHT))

    clock = pygame.time.Clock()
    f_title = pygame.font.SysFont('Arial', 24, True)
    f_st = pygame.font.SysFont('Arial', 22, True)
    f_sensor = pygame.font.SysFont('Arial', 20, True)
    f_btn = pygame.font.SysFont('Arial', 18, True)
    f_menu = pygame.font.SysFont('Arial', 17, True)
    f_modal_title = pygame.font.SysFont('Arial', 22, True)
    f_modal_sub = pygame.font.SysFont('Arial', 15)
    f_log = pygame.font.SysFont('Consolas', 15)
    f_log_title = pygame.font.SysFont('Arial', 20, True)

    face = AnimatedFace(512, 250)
    btn_w = TouchButton((252, 230, 240, 75), 'Siram Air (Pompa)', (25, 118, 210), (220, 50, 50), '💧')
    btn_m = TouchButton((532, 230, 240, 75), 'Semprot Mist', (0, 137, 123), (220, 50, 50), '🌫️')
    btn_close_modal = pygame.Rect(412, 345, 200, 48)

    btn_hamburger = pygame.Rect(20, 15, 52, 44)
    menu_open = False
    show_manual_modal = False
    show_log_modal = False
    show_masking_modal = False

    # Masking State
    masking_enabled = False
    masked_mood = 'happy'

    # Menu Dropdown Items (6 items)
    dropdown_rect = pygame.Rect(18, 65, 240, 304)
    item_siram_rect = pygame.Rect(20, 68, 236, 46)
    item_masking_rect = pygame.Rect(20, 118, 236, 46)
    item_master_rect = pygame.Rect(20, 168, 236, 46)
    item_mic_rect = pygame.Rect(20, 218, 236, 46)
    item_log_rect = pygame.Rect(20, 268, 236, 46)
    item_logout_rect = pygame.Rect(20, 318, 236, 46)

    # Modal Log elements
    btn_close_log = pygame.Rect(422, 510, 180, 45)
    btn_x_log = pygame.Rect(875, 45, 45, 40)

    # Modal Masking elements
    modal_masking_rect = pygame.Rect(202, 90, 620, 390)
    btn_masking_toggle = pygame.Rect(242, 165, 540, 52)
    btn_mood_happy = pygame.Rect(242, 245, 122, 65)
    btn_mood_neutral = pygame.Rect(381, 245, 122, 65)
    btn_mood_thirsty = pygame.Rect(520, 245, 122, 65)
    btn_mood_critical = pygame.Rect(659, 245, 122, 65)
    btn_close_masking = pygame.Rect(412, 395, 200, 48)

    fb = FirebaseSync()
    last_log_update = 0.0
    cached_logs = []
    current_master = True

    def do_logout():
        fb.running = False
        print("Logout: Menghentikan display...")
        pygame.quit()
        sys.exit(0)

    while True:
        dt = clock.tick(FPS) / 1000.0
        now = time.time()

        if show_log_modal and (now - last_log_update > 0.6):
            cached_logs = get_recent_logs(15)
            last_log_update = now

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: do_logout()
            elif ev.type == pygame.KEYDOWN and ev.key in (pygame.K_ESCAPE, pygame.K_q): do_logout()
            elif ev.type in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
                pos = ev.pos if ev.type == pygame.MOUSEBUTTONDOWN else (int(ev.x * WIDTH), int(ev.y * HEIGHT))

                # Interaksi Modal Masking
                if show_masking_modal:
                    if btn_masking_toggle.collidepoint(pos):
                        masking_enabled = not masking_enabled
                    elif btn_mood_happy.collidepoint(pos):
                        masked_mood = 'happy'
                        masking_enabled = True
                    elif btn_mood_neutral.collidepoint(pos):
                        masked_mood = 'neutral'
                        masking_enabled = True
                    elif btn_mood_thirsty.collidepoint(pos):
                        masked_mood = 'thirsty'
                        masking_enabled = True
                    elif btn_mood_critical.collidepoint(pos):
                        masked_mood = 'critical'
                        masking_enabled = True
                    elif btn_close_masking.collidepoint(pos) or not modal_masking_rect.collidepoint(pos):
                        show_masking_modal = False
                    continue

                # Interaksi Modal Log
                if show_log_modal:
                    if btn_close_log.collidepoint(pos) or btn_x_log.collidepoint(pos) or not pygame.Rect(80, 35, 864, 530).collidepoint(pos):
                        show_log_modal = False
                    continue

                # Interaksi Modal Siram Manual
                if show_manual_modal:
                    if btn_w.handle_touch(pos):
                        btn_w.is_active = not btn_w.is_active
                        fb.set_water_pump(btn_w.is_active)
                    elif btn_m.handle_touch(pos):
                        btn_m.is_active = not btn_m.is_active
                        fb.set_mist_pump(btn_m.is_active)
                    elif btn_close_modal.collidepoint(pos) or not pygame.Rect(212, 110, 600, 310).collidepoint(pos):
                        show_manual_modal = False
                    continue

                # Interaksi Dropdown Menu
                if menu_open:
                    if item_siram_rect.collidepoint(pos):
                        menu_open = False
                        show_manual_modal = True
                    elif item_masking_rect.collidepoint(pos):
                        menu_open = False
                        show_masking_modal = True
                    elif item_master_rect.collidepoint(pos):
                        fb.set_master(not current_master)
                    elif item_mic_rect.collidepoint(pos):
                        # Toggle flag mute mic
                        flag = '/tmp/assistant_mic_muted'
                        if os.path.exists(flag):
                            try: os.remove(flag)
                            except: pass
                        else:
                            try:
                                with open(flag, 'w') as f: f.write('1')
                            except: pass
                    elif item_log_rect.collidepoint(pos):
                        menu_open = False
                        show_log_modal = True
                        cached_logs = get_recent_logs(15)
                        last_log_update = now
                    elif item_logout_rect.collidepoint(pos):
                        do_logout()
                    elif btn_hamburger.collidepoint(pos): menu_open = False
                    else: menu_open = False
                    continue

                if btn_hamburger.collidepoint(pos): menu_open = True
                elif pos[1] < 220: face.react('pet')
                elif 220 <= pos[1] < 420: face.react('poke')

        face.is_talking = os.path.exists('/tmp/smile_talking')
        s, auto_st_txt, auto_st_col, auto_mood, wp, mp, current_master = fb.snapshot()
        
        # Logika Masking vs Sensor
        if masking_enabled:
            current_mood = masked_mood
            st_txt = f"[MASKING] {MOOD_COLORS[current_mood]['status']}"
            st_col = MOOD_COLORS[current_mood]['status_color']
        else:
            current_mood = auto_mood
            st_txt = auto_st_txt
            st_col = auto_st_col

        face.set_mood(current_mood)
        btn_w.is_active, btn_m.is_active = wp, mp
        bob_y = face.update(dt)

        screen.fill(BG_COLOR)
        face.draw(screen, bob_y)
        
        # Hamburger Menu Button
        pygame.draw.rect(screen, (240, 242, 245), btn_hamburger, border_radius=8)
        for ly in [btn_hamburger.y + 11, btn_hamburger.y + 21, btn_hamburger.y + 31]:
            pygame.draw.line(screen, (60, 65, 75), (btn_hamburger.x + 12, ly), (btn_hamburger.x + 40, ly), 3)

        # Status & Sensors
        st_surf = f_st.render(st_txt, True, st_col)
        screen.blit(st_surf, st_surf.get_rect(center=(WIDTH // 2, 425)))
        
        # Indicator bar
        pygame.draw.rect(screen, PANEL_COLOR, (120, 480, 784, 80), border_radius=12)
        txts = [f"Suhu: {s['t']:.1f}°C", f"Hum: {s['h']:.0f}%", f"Tanah: {s['sm']:.0f}%", f"pH: {s['ph']:.1f}"]
        for i, t in enumerate(txts):
            screen.blit(f_sensor.render(t, True, (40, 40, 40)), (150 + i * 190, 505))

        # Dropdown Menu (6 items)
        if menu_open:
            pygame.draw.rect(screen, (255, 255, 255), dropdown_rect, border_radius=10)
            pygame.draw.rect(screen, (180, 185, 195), dropdown_rect, 2, border_radius=10)
            
            # 1. Siram Manual
            pygame.draw.rect(screen, (245, 248, 255), item_siram_rect, border_radius=8)
            screen.blit(f_menu.render('💧 Siram Manual', True, (30, 100, 210)), (34, 81))
            pygame.draw.line(screen, (220, 225, 230), (25, 115), (250, 115), 1)

            # 2. Masking Ekspresi
            pygame.draw.rect(screen, (254, 250, 240), item_masking_rect, border_radius=8)
            screen.blit(f_menu.render('🎭 Masking Ekspresi', True, (210, 110, 25)), (34, 131))
            pygame.draw.line(screen, (220, 225, 230), (25, 165), (250, 165), 1)

            # 3. Master Control (/master)
            master_label = f"⚙️ Master: {'AUTO' if current_master else 'MANUAL'}"
            master_col = (30, 160, 60) if current_master else (220, 40, 50)
            pygame.draw.rect(screen, (245, 252, 245) if current_master else (255, 245, 245), item_master_rect, border_radius=8)
            screen.blit(f_menu.render(master_label, True, master_col), (34, 181))
            pygame.draw.line(screen, (220, 225, 230), (25, 215), (250, 215), 1)

            # 4. On / Off Mic Asisten
            mic_muted = os.path.exists('/tmp/assistant_mic_muted')
            mic_label = f"🎙️ Mic AI: {'MATI' if mic_muted else 'AKTIF'}"
            mic_col = (220, 40, 50) if mic_muted else (30, 160, 60)
            pygame.draw.rect(screen, (255, 245, 245) if mic_muted else (245, 252, 245), item_mic_rect, border_radius=8)
            screen.blit(f_menu.render(mic_label, True, mic_col), (34, 231))
            pygame.draw.line(screen, (220, 225, 230), (25, 265), (250, 265), 1)

            # 5. Log Asisten AI
            pygame.draw.rect(screen, (245, 252, 248), item_log_rect, border_radius=8)
            screen.blit(f_menu.render('📋 Log Asisten AI', True, (25, 135, 84)), (34, 281))
            pygame.draw.line(screen, (220, 225, 230), (25, 315), (250, 315), 1)

            # 6. Logout
            pygame.draw.rect(screen, (255, 246, 246), item_logout_rect, border_radius=8)
            screen.blit(f_menu.render('🚪 Logout', True, (210, 40, 50)), (34, 331))

        # Modal Siram Manual
        if show_manual_modal:
            pygame.draw.rect(screen, (0,0,0,120), (0,0,WIDTH,HEIGHT))
            pygame.draw.rect(screen, (255,255,255), (212, 110, 600, 310), border_radius=18)
            btn_w.draw(screen, f_btn, dt); btn_m.draw(screen, f_btn, dt)
            pygame.draw.rect(screen, (235,238,242), btn_close_modal, border_radius=10)
            screen.blit(f_btn.render('Tutup', True, (60,65,75)), btn_close_modal.move(75, 15))

        # Modal Masking Ekspresi
        if show_masking_modal:
            pygame.draw.rect(screen, (0, 0, 0, 130), (0, 0, WIDTH, HEIGHT))
            pygame.draw.rect(screen, (255, 255, 255), modal_masking_rect, border_radius=18)
            pygame.draw.rect(screen, (200, 205, 215), modal_masking_rect, 2, border_radius=18)

            # Header Masking
            t_m_title = f_modal_title.render('🎭 Masking Ekspresi Wajah', True, (35, 40, 50))
            screen.blit(t_m_title, (modal_masking_rect.x + 35, modal_masking_rect.y + 22))

            t_m_sub = f_modal_sub.render('Ubah ekspresi secara manual di luar pembacaan data sensor:', True, (100, 105, 115))
            screen.blit(t_m_sub, (modal_masking_rect.x + 35, modal_masking_rect.y + 54))

            # Tombol Saklar ON / OFF Masking
            if masking_enabled:
                pygame.draw.rect(screen, (40, 167, 69), btn_masking_toggle, border_radius=12)
                t_sw = f_btn.render('STATUS: AKTIF (Tekan untuk Matikan / Pakai Sensor)', True, (255, 255, 255))
            else:
                pygame.draw.rect(screen, (108, 117, 125), btn_masking_toggle, border_radius=12)
                t_sw = f_btn.render('STATUS: NONAKTIF (Mengikuti Data Sensor Otomatis)', True, (255, 255, 255))
            screen.blit(t_sw, t_sw.get_rect(center=btn_masking_toggle.center))

            # 3 Pilihan Mood
            mood_configs = [
                (btn_mood_happy, 'happy', '😊 Normal', (40, 167, 69)),
                (btn_mood_thirsty, 'thirsty', '😢 Menyimpang', (30, 130, 230)),
                (btn_mood_critical, 'critical', '😠 Kritis', (220, 53, 69)),
            ]

            for rect, m_key, m_label, col in mood_configs:
                is_selected = (masking_enabled and masked_mood == m_key)
                bg_col = col if is_selected else (245, 247, 250)
                txt_col = (255, 255, 255) if is_selected else (45, 50, 60)
                pygame.draw.rect(screen, bg_col, rect, border_radius=10)
                border_col = col if is_selected else (200, 205, 215)
                border_w = 3 if is_selected else 1
                pygame.draw.rect(screen, border_col, rect, border_w, border_radius=10)
                txt_s = f_btn.render(m_label, True, txt_col)
                screen.blit(txt_s, txt_s.get_rect(center=rect.center))

            # Info keterangan singkat
            info_txt = '💡 Saat Aktif, wajah mengunci pilihan di atas. Saat Nonaktif, wajah mengikuti sensor.'
            screen.blit(f_modal_sub.render(info_txt, True, (120, 125, 135)), (modal_masking_rect.x + 35, modal_masking_rect.y + 330))

            # Tombol Simpan & Tutup
            pygame.draw.rect(screen, (235, 238, 242), btn_close_masking, border_radius=10)
            pygame.draw.rect(screen, (190, 195, 205), btn_close_masking, 1, border_radius=10)
            t_close_m = f_btn.render('Simpan & Tutup', True, (45, 50, 60))
            screen.blit(t_close_m, t_close_m.get_rect(center=btn_close_masking.center))

        # Modal Log Asisten AI
        if show_log_modal:
            pygame.draw.rect(screen, (0, 0, 0, 140), (0, 0, WIDTH, HEIGHT))
            log_box = pygame.Rect(80, 35, 864, 530)
            pygame.draw.rect(screen, (24, 28, 35), log_box, border_radius=16)
            pygame.draw.rect(screen, (50, 60, 75), log_box, 2, border_radius=16)

            pygame.draw.circle(screen, (40, 200, 100), (115, 65), 7)
            t_title = f_log_title.render('Aktivitas & Log Asisten AI (Live)', True, (240, 245, 250))
            screen.blit(t_title, (135, 52))

            pygame.draw.rect(screen, (45, 52, 65), btn_x_log, border_radius=8)
            t_x = f_btn.render('✕', True, (200, 210, 220))
            screen.blit(t_x, t_x.get_rect(center=btn_x_log.center))

            pygame.draw.line(screen, (45, 55, 70), (95, 90), (925, 90), 1)

            for i, line in enumerate(cached_logs):
                if '[User]' in line: col = (110, 235, 140)
                elif '[AI]' in line: col = (255, 215, 100)
                elif '[Mendengarkan' in line: col = (120, 185, 255)
                elif 'error' in line.lower() or 'exception' in line.lower() or 'died' in line.lower(): col = (255, 120, 120)
                else: col = (205, 215, 225)

                txt_disp = line if len(line) <= 90 else line[:87] + '...'
                l_surf = f_log.render(txt_disp, True, col)
                screen.blit(l_surf, (105, 102 + i * 26))

            pygame.draw.rect(screen, (45, 55, 72), btn_close_log, border_radius=10)
            pygame.draw.rect(screen, (80, 95, 120), btn_close_log, 1, border_radius=10)
            t_close = f_btn.render('Tutup Log', True, (240, 245, 250))
            screen.blit(t_close, t_close.get_rect(center=btn_close_log.center))

        pygame.display.flip()

if __name__ == '__main__':
    main()
