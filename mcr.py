#!/usr/bin/env python3
"""
================================================================================
MCR - THE BLACK PARADE: PEPE THE DRUM MAJOR
Grand Dark Aesthetic ASCII Engine, Radiant Moon, Golden Baton & Giant Fireworks
================================================================================
Peningkatan Utama:
1. Kembang Api Tinggi & Ledakan Raksasa (Mulai Detik 20 ke Atas / t >= 20.0s):
   - Roket meluncur tinggi ke langit atas (H * 0.08 .. 0.27) dengan ekor komet
     emas-perak panjang (^ ! | : .).
   - Meledak menjadi 110–150 jejak bunga api radial berlapis (Inti Bintang,
     Krisan Raksasa, Mahkota Willow Emas, dan Cincin Shockwave ASCII) dengan
     diameter ledakan sangat besar serta sub-ledakan kerlip (crackle) di ujungnya.
2. Ujung Mayoret Bersinar Kuning Keemasan (Golden Mayoret Baton & Mace):
   - Ujung bawah tongkat mayoret (Mace Bulb) dan ujung atas tombak tongkat
     bercahaya kuning emas terang ((255, 225, 65) - (255, 248, 150)) lengkap
     dengan lingkaran Halo ASCII kuning berputar dan jejak komet percikan emas.
3. Bulan Sabit Bersinar Terang (Radiant Glowing Crescent Moon):
   - Bulan sabit dirender di layer bloom utama dengan korona cahaya radial,
     3 cincin halo ASCII konsentris yang berdenyut lembut, dan berkas sinar
     bulan (ASCII Moonbeams) yang menyinari siluet Pepe.
4. Peningkatan Detail & Animasi Hidup pada Gambar ASCII Pepe:
   - Dual-Rim Lighting: Sisi kiri diterangi cahaya bulan perak-biru, sisi kanan
     diterangi pantulan emas dari tongkat mayoret.
   - Kilau perak berjalan (travelling glint) di sepanjang tulang kepang dada (=),
     kilatan mata tengkorak halus, gelombang kain seragam tertiup angin malam,
     helai bulu topi (plume wisps) yang terlepas, dan pusaran aura parade di
     sekeliling tubuh Pepe agar animasi ASCII selalu hidup dan tidak sepi.
5. Transisi Masuk & Gerakan Tentara Ekstra Halus (Sub-Pixel Smooth Kinematics):
   - Pergerakan sub-piksel mulus (tanpa patah-patah grid snapping), amplop
     blending transisi-ke-langkah (march_env) tanpa hentakan, dan kurva harmonik
     kosinus mulus (0.36 Hz).
================================================================================
Kontrol:
  F11   : Toggle Fullscreen / Windowed
  Space : Pause / Resume
  R     : Ulangi dari awal (t = 0.0s, transisi masuk)
  F     : Lompat langsung ke detik 20.0 (uji cepat Kembang Api Raksasa)
  S     : Simpan screenshot PNG
  Esc   : Keluar
================================================================================
"""

import sys
import os
import math
import random
import time
from typing import List, Tuple, Dict

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

try:
    import pygame
except ImportError:
    print("Error: Library pygame dibutuhkan. Jalankan: pip install pygame")
    sys.exit(1)

try:
    from pepe_data import PEPE_POINTS, PEPE_SPRITE_COLS, PEPE_SPRITE_ROWS
except ImportError:
    print("Error: File pepe_data.py tidak ditemukan di folder yang sama.")
    sys.exit(1)


# ==============================================================================
# KONFIGURASI KANVAS & TEMA GELAP (DARK AESTHETIC)
# ==============================================================================
W, H = 1200, 864
FPS = 60

CW, CH = 5, 6
FONT_PX = 9
GRID_COLS = W // CW   # 240 kolom
GRID_ROWS = H // CH   # 144 baris

TAU = math.pi * 2.0

# Opacity latar belakang tetap rendah (~24%) agar tema gelap & cahaya ASCII menonjol
BG_OPACITY = 0.24

# Karakter berdasarkan kepadatan cahaya (dari black_hole.py & cat_knight.py)
POOLS = ["1il!;:", "rtfjcvxz=+", "aeoun0{}[]<>", "08B$#&%Q@"]
MONO_FONTS = "consolas,menlo,dejavusansmono,couriernew,monospace"

# Waktu fase animasi (dalam detik)
FLASH_TIME = 5.4       # Momen cincin gelombang kejut (shockwave) memancar
MARCH_START = 6.0      # Mulai fase parade penuh (dengan blending halus sejak 4.6s)
FIREWORKS_START = 20.0 # Kembang api raksasa mulai meluncur dari detik ke-20 ke atas


# ==============================================================================
# FUNGSI MATEMATIKA & PROSEDURAL
# ==============================================================================
def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def smooth(x: float) -> float:
    """Hermite smoothstep (0..1)."""
    x = clamp(x, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


def smoother(x: float) -> float:
    """Quintic smoothstep (C2-continuous) untuk transisi & gerakan ekstra halus."""
    x = clamp(x, 0.0, 1.0)
    return x * x * x * (x * (x * 6.0 - 15.0) + 10.0)


def ripple(a: float, b: float, t: float) -> float:
    """Gelombang organik multi-harmonik dari black_hole.py."""
    return (
        math.sin(a + 0.9 * math.sin(b + 1.3 * t)) * 0.5
        + math.sin(2.3 * a - b + 0.7 * t) * 0.3
        + math.sin(4.1 * a + 1.7 * b - 1.1 * t) * 0.2
    )


def tangent_char(dx: float, dy: float) -> str:
    """Memilih huruf garis singgung (/ \\ | -) berdasarkan arah vektor."""
    s = math.degrees(math.atan2(-dy, dx)) % 180.0
    if s < 22.5 or s >= 157.5:
        return '-'
    elif s < 67.5:
        return '/'
    elif s < 112.5:
        return '|'
    else:
        return '\\'


def rotate_point(x: float, y: float, px: float, py: float, angle: float) -> Tuple[float, float]:
    """Rotasi 2D presisi floating-point pada titik sendi (px, py)."""
    ca = math.cos(angle)
    sa = math.sin(angle)
    dx = x - px
    dy = y - py
    return px + dx * ca - dy * sa, py + dx * sa + dy * ca


def blur_surface(surf: pygame.Surface, k: int, radius: int) -> pygame.Surface:
    """Downscale + Gaussian blur untuk efek cahaya bloom lembut ala JIN2."""
    sw, sh = max(1, W // k), max(1, H // k)
    small = pygame.transform.smoothscale(surf, (sw, sh))
    if hasattr(pygame.transform, "gaussian_blur"):
        small = pygame.transform.gaussian_blur(small, max(1, radius // k))
    return pygame.transform.smoothscale(small, (W, H))


def glow_tint(surf: pygame.Surface, amount: float) -> pygame.Surface:
    """Mengatur intensitas layer bloom sebelum di-blend secara aditif."""
    layer = surf.copy()
    val = int(clamp(amount * 255.0, 0.0, 255.0))
    layer.fill((val, val, val), special_flags=pygame.BLEND_MULT)
    return layer


# ==============================================================================
# SISTEM KEMBANG API BERBERVARIASI (RENDAH/SEDANG/TINGGI & KECIL/SEDANG/BESAR)
# ==============================================================================
class ASCIIFireworkRocket:
    """Roket kembang api ASCII dengan variasi ketinggian (rendah, sedang, tinggi)
    dan variasi ukuran ledakan (kecil, sedang, besar)."""

    PALETTES = [
        # 1. Imperial Gold, Bright Yellow & Warm Amber Crown
        [(255, 235, 95), (255, 180, 55), (255, 250, 200), (255, 130, 40)],
        # 2. Black Parade Crimson, Rose Gold & Platinum Silver
        [(255, 65, 90), (235, 242, 255), (255, 150, 165), (255, 215, 120)],
        # 3. Supernova Cyan, Electric Violet & Starlight White
        [(110, 230, 255), (195, 130, 255), (240, 250, 255), (255, 210, 110)],
        # 4. Emerald Jade, Golden Champagne & Mint Glow
        [(95, 250, 165), (255, 230, 115), (210, 255, 230), (255, 185, 80)],
    ]

    def __init__(
        self,
        rng: random.Random,
        launch_x: float,
        launch_y: float,
        altitude_tier: str = 'medium',
        size_tier: str = 'medium',
    ):
        self.rng = rng
        self.x = launch_x
        self.y = launch_y
        self.start_x = launch_x
        self.altitude_tier = altitude_tier
        self.size_tier = size_tier

        # 1. Variasi Ketinggian: Rendah (di atas gedung), Sedang (tengah), Tinggi (atas)
        if altitude_tier == 'low':
            self.target_y = rng.uniform(H * 0.43, H * 0.55)
        elif altitude_tier == 'medium':
            self.target_y = rng.uniform(H * 0.24, H * 0.40)
        else:  # 'high'
            self.target_y = rng.uniform(H * 0.08, H * 0.22)

        # 2. Variasi Ukuran Ledakan: Kecil, Sedang, Besar
        if size_tier == 'small':
            self.scale = rng.uniform(0.42, 0.60)
            self.particle_mult = 0.46
            self.tail_base = 4
        elif size_tier == 'medium':
            self.scale = rng.uniform(0.74, 0.96)
            self.particle_mult = 0.74
            self.tail_base = 7
        else:  # 'large'
            self.scale = rng.uniform(1.14, 1.40)
            self.particle_mult = 1.05
            self.tail_base = 10

        self.vx = rng.uniform(-14.0, 14.0)
        dist_y = max(120.0, launch_y - self.target_y)
        self.vy = -math.sqrt(2.0 * 195.0 * dist_y) * rng.uniform(0.96, 1.05)

        self.palette = rng.choice(self.PALETTES)
        self.style = rng.choice(['grand_chrysanthemum', 'royal_willow', 'supernova_ring', 'crossette_crown'])
        self.exploded = False
        self.dead = False
        self.flash_energy = 0.0
        self.shock_radius = 0.0
        self.shock_alpha = 0.0
        self.burst_x = launch_x
        self.burst_y = self.target_y
        self.trail_history: List[Tuple[float, float]] = []
        self.AscendingSparks: List[Dict] = []
        self.sparks: List[Dict] = []

    def update(self, dt: float, t: float):
        if not self.exploded:
            self.trail_history.append((self.x, self.y))
            max_trail = 10 if self.altitude_tier == 'low' else (13 if self.altitude_tier == 'medium' else 16)
            if len(self.trail_history) > max_trail:
                self.trail_history.pop(0)

            if self.rng.random() < 0.70:
                self.AscendingSparks.append({
                    'x': self.x + self.rng.uniform(-3.0, 3.0),
                    'y': self.y + self.rng.uniform(0.0, 6.0),
                    'vx': self.rng.uniform(-20.0, 20.0),
                    'vy': self.rng.uniform(18.0, 58.0),
                    'age': 0.0,
                    'max_age': self.rng.uniform(0.22, 0.48),
                })

            for asp in self.AscendingSparks[:]:
                asp['age'] += dt
                asp['x'] += asp['vx'] * dt
                asp['y'] += asp['vy'] * dt
                if asp['age'] >= asp['max_age']:
                    self.AscendingSparks.remove(asp)

            self.x += self.vx * dt + math.sin(t * 9.0 + self.start_x) * 12.0 * dt
            self.y += self.vy * dt
            self.vy += 185.0 * dt

            if self.y <= self.target_y or self.vy >= -35.0:
                self._explode()
        else:
            self.flash_energy = max(0.0, self.flash_energy - dt * 2.6)
            if self.shock_alpha > 0.01:
                self.shock_radius += dt * 240.0 * self.scale
                self.shock_alpha = max(0.0, self.shock_alpha - dt * 1.55)

            for asp in self.AscendingSparks[:]:
                asp['age'] += dt
                if asp['age'] >= asp['max_age']:
                    self.AscendingSparks.remove(asp)

            alive_count = 0
            for sp in self.sparks:
                sp['age'] += dt
                if sp['age'] >= sp['max_age']:
                    continue
                alive_count += 1

                if int(sp['age'] * 36) != int((sp['age'] - dt) * 36):
                    sp['tail'].append((sp['x'], sp['y']))
                    if len(sp['tail']) > sp['tail_len']:
                        sp['tail'].pop(0)

                drag = sp['drag']
                sp['vx'] *= (1.0 - drag * dt)
                sp['vy'] = sp['vy'] * (1.0 - drag * dt) + sp['gravity'] * dt
                sp['x'] += sp['vx'] * dt
                sp['y'] += sp['vy'] * dt

            if alive_count == 0 and self.flash_energy <= 0.01:
                self.dead = True

    def _explode(self):
        self.exploded = True
        self.burst_x = self.x
        self.burst_y = self.y
        sc = self.scale
        pm = self.particle_mult
        self.flash_energy = 0.95 * sc
        self.shock_radius = 6.0
        self.shock_alpha = min(0.95, 0.72 * sc)
        rng = self.rng

        if self.style == 'supernova_ring':
            raw_layers = [
                (26, 120.0 * sc, 0, False),
                (48, 225.0 * sc, 1, True),
                (60, 310.0 * sc, 2, True),
            ]
        elif self.style == 'royal_willow':
            raw_layers = [
                (28, 130.0 * sc, 2, False),
                (54, 230.0 * sc, 0, False),
                (50, 315.0 * sc, 1, False),
            ]
        else:
            raw_layers = [
                (28, 125.0 * sc, 2, False),
                (54, 230.0 * sc, 0, False),
                (52, 320.0 * sc, 1, False),
            ]

        for raw_count, base_speed, pal_idx, is_strict_ring in raw_layers:
            count = max(10, int(raw_count * pm))
            for i in range(count):
                ang = (i / float(count)) * TAU + rng.uniform(-0.07, 0.07)
                if is_strict_ring:
                    spd = base_speed * rng.uniform(0.92, 1.08)
                else:
                    spd = base_speed * (0.45 + 0.65 * math.sqrt(rng.random()))

                col = self.palette[(pal_idx + i) % len(self.palette)]
                is_willow = (self.style == 'royal_willow')
                grav = (72.0 if is_willow else 44.0) * (0.75 + 0.25 * sc)
                drag = 0.92 if is_willow else 1.08
                max_age = (rng.uniform(2.0, 3.1) if is_willow else rng.uniform(1.5, 2.5)) * (0.72 + 0.28 * sc)

                self.sparks.append({
                    'x': self.x,
                    'y': self.y,
                    'vx': math.cos(ang) * spd,
                    'vy': math.sin(ang) * spd,
                    'color': col,
                    'age': 0.0,
                    'max_age': max_age,
                    'gravity': grav,
                    'drag': drag,
                    'tail': [],
                    'tail_len': self.tail_base + (2 if is_willow else 0),
                    'seed': rng.randint(0, 1000),
                })


# ==============================================================================
# MESIN UTAMA ANIMASI MCR BLACK PARADE
# ==============================================================================
class MCRBlackParadeApp:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("MCR - The Black Parade (Grand Dark ASCII Art)")

        info = pygame.display.Info()
        self.screen_w = info.current_w if info.current_w > 0 else W
        self.screen_h = info.current_h if info.current_h > 0 else H

        self.is_fullscreen = True
        self.window = pygame.display.set_mode(
            (self.screen_w, self.screen_h),
            pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE
        )

        # Surface utama & buffer trail dengan persistensi lebih halus (0.44)
        self.canvas_surf = pygame.Surface((W, H))
        self.ascii_layer = pygame.Surface((W, H))
        self.trail_surf = pygame.Surface((W, H))
        self.trail_fade = (int(0.44 * 255),) * 3

        self.font = self._load_mono_font(FONT_PX)
        self.glyph_cache: Dict[Tuple[str, Tuple[int, int, int]], pygame.Surface] = {}

        # Posisi Bulan Bersinar di langit kiri atas
        self.moon_cx = int(W * 0.16)
        self.moon_cy = int(H * 0.18)

        # 1. Bangun latar belakang kota malam dengan OPACITY RENDAH & Korona Bulan
        self.base_y = int(H * 0.87)
        self.bg_static_surf, self.work_windows, self.sky_stars = self._build_dark_cityscape()

        # 2. Siapkan animasi ASCII aesthetic (Bulan Bersinar, Aura Parade, Plume Wisps, dll.)
        self._init_aesthetic_ascii_fx()

        # 3. Siapkan titik-titik Pepe dengan peningkatan detail & ujung mayoret kuning emas
        self.sprite_offset_c = (GRID_COLS - PEPE_SPRITE_COLS) // 2 + 4
        self.sprite_offset_r = (GRID_ROWS - PEPE_SPRITE_ROWS) // 2 + 4

        cx_px = (self.sprite_offset_c + 64) * CW
        cy_px = (self.sprite_offset_r + 54) * CH

        self.pepe_nodes = []
        for idx, pt in enumerate(PEPE_POINTS):
            c, r, ch, col, is_edge, tag = pt
            tx = (self.sprite_offset_c + c) * CW
            ty = (self.sprite_offset_r + r) * CH
            dx = (tx - cx_px) / float(H)
            dy = (ty - cy_px) / float(H)
            rad = math.hypot(dx, dy)
            ang = math.atan2(dy, dx)
            around = ((ang + math.pi / 2.0) % TAU) / TAU
            t_ch = tangent_char(-math.sin(ang), math.cos(ang))

            # Apakah titik ini bagian dari Ujung Mayoret (Mace Bulb bawah atau Ujung Atas Tongkat)?
            is_mace_bulb = (tag == 7 and r >= 57 and c <= 90)
            is_baton_tip = (tag == 8 and r <= 27)
            is_frogging_rib = ((tag == 5 or tag == 9) and ch == '=')

            dark_col = self._tune_enhanced_pepe_color(
                c, r, col, ch, is_edge, tag, is_mace_bulb, is_baton_tip, is_frogging_rib
            )

            # Karakter lebih padat & berkilau untuk ujung mayoret kuning emas
            if is_mace_bulb:
                ch = '@' if (r + c) % 2 == 0 else ('0' if is_edge == 0 else '*')
            elif is_baton_tip and r <= 19:
                ch = '*' if (r + c) % 2 == 0 else '+'

            self.pepe_nodes.append({
                'c': c,
                'r': r,
                'tx': float(tx),
                'ty': float(ty),
                'ch': ch,
                't_ch': t_ch,
                'color': dark_col,
                'is_edge': is_edge,
                'tag': tag,
                'is_mace_bulb': is_mace_bulb,
                'is_baton_tip': is_baton_tip,
                'is_rib': is_frogging_rib,
                'rad': rad,
                'ang': ang,
                'around': around,
                'hsh': (c * 37 + r * 101 + idx) % 12,
            })

        # Sel-sel cincin shockwave saat FLASH_TIME
        self.shock_cells = []
        for gr in range(0, GRID_ROWS, 2):
            for gc in range(0, GRID_COLS, 2):
                px = gc * CW
                py = gr * CH
                sr = math.hypot((px - cx_px) / H, (py - cy_px) / H)
                sang = math.atan2(py - cy_px, px - cx_px)
                tch = tangent_char(-math.sin(sang), math.cos(sang))
                self.shock_cells.append((px, py, sr, tch))

        # Pelindung Siluet Pepe (2D Distance Transform) agar Kembang Api TIDAK PERNAH
        # menutupi gambar ASCII Pepe ketika meledak di dekatnya
        self.pepe_shield = self._build_pepe_protection_shield()

        # 4. Sistem Kembang Api Bervariasi (Mulai detik 20 ke atas)
        self.fw_rng = random.Random(1986)
        self.fireworks: List[ASCIIFireworkRocket] = []
        self.next_fw_time = FIREWORKS_START

        # Partikel dinamis dari karakter Pepe (percikan emas mayoret, bulu topi, riak langkah)
        self.baton_sparks: List[Dict] = []
        self.plume_wisps: List[Dict] = []
        self.step_ripples: List[Dict] = []
        self.last_step_half = -1

        self.time_elapsed = 0.0
        self.is_paused = False
        # Frekuensi langkah diperhalus & ditenangkan (0.36 Hz = 2.78 detik per siklus penuh)
        self.march_freq = 0.36
        self.clock = pygame.time.Clock()

    def _load_mono_font(self, size: int) -> pygame.font.Font:
        for name in MONO_FONTS.split(','):
            try:
                f = pygame.font.SysFont(name.strip(), size, bold=True)
                if f:
                    return f
            except Exception:
                continue
        return pygame.font.Font(None, size)

    def _build_pepe_protection_shield(self) -> List[List[float]]:
        """Membangun peta jarak 2D (Chamfer Distance Transform) di sekitar siluet Pepe
        dan jangkauan gerak kaki/tangannya agar ledakan kembang api di dekat Pepe
        secara otomatis meredup/terhalang di belakangnya dan TIDAK PERNAH menutupi Pepe."""
        INF = 999.0
        dist = [[INF for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]

        for node in self.pepe_nodes:
            gc = int(node['tx'] // CW)
            gr = int(node['ty'] // CH)
            tag = node['tag']
            # Tambahkan margin ekstra untuk bagian kaki & tangan yang berayun saat parade
            pad_c = 3 if tag in (6, 7, 8, 9, 10) else 2
            pad_r = 4 if tag in (9, 10) else 2
            for dr in range(-pad_r, pad_r + 1):
                rr = gr + dr
                if 0 <= rr < GRID_ROWS:
                    for dc in range(-pad_c, pad_c + 1):
                        cc = gc + dc
                        if 0 <= cc < GRID_COLS:
                            dist[rr][cc] = 0.0

        # Pass 1: Kiri-Atas ke Kanan-Bawah
        for gr in range(GRID_ROWS):
            row = dist[gr]
            prev_row = dist[gr - 1] if gr > 0 else None
            for gc in range(GRID_COLS):
                d = row[gc]
                if d == 0.0:
                    continue
                if gc > 0 and row[gc - 1] + 1.0 < d:
                    d = row[gc - 1] + 1.0
                if prev_row is not None:
                    if prev_row[gc] + 1.0 < d:
                        d = prev_row[gc] + 1.0
                    if gc > 0 and prev_row[gc - 1] + 1.414 < d:
                        d = prev_row[gc - 1] + 1.414
                    if gc + 1 < GRID_COLS and prev_row[gc + 1] + 1.414 < d:
                        d = prev_row[gc + 1] + 1.414
                row[gc] = d

        # Pass 2: Kanan-Bawah ke Kiri-Atas
        for gr in range(GRID_ROWS - 1, -1, -1):
            row = dist[gr]
            next_row = dist[gr + 1] if gr + 1 < GRID_ROWS else None
            for gc in range(GRID_COLS - 1, -1, -1):
                d = row[gc]
                if d == 0.0:
                    continue
                if gc + 1 < GRID_COLS and row[gc + 1] + 1.0 < d:
                    d = row[gc + 1] + 1.0
                if next_row is not None:
                    if next_row[gc] + 1.0 < d:
                        d = next_row[gc] + 1.0
                    if gc + 1 < GRID_COLS and next_row[gc + 1] + 1.414 < d:
                        d = next_row[gc + 1] + 1.414
                    if gc > 0 and next_row[gc - 1] + 1.414 < d:
                        d = next_row[gc - 1] + 1.414
                row[gc] = d

        # Konversi jarak sel menjadi faktor visibilitas kembang api (0.0 di dalam/tepi Pepe -> 1.0 di luar)
        shield = [[1.0 for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        for gr in range(GRID_ROWS):
            for gc in range(GRID_COLS):
                d = dist[gr][gc]
                if d <= 1.5:
                    shield[gr][gc] = 0.0
                elif d < 9.5:
                    shield[gr][gc] = smooth((d - 1.5) / 8.0)
                else:
                    shield[gr][gc] = 1.0
        return shield

    def _get_pepe_shield(self, px: float, py: float) -> float:
        """Mengembalikan faktor transmisi (0.0 .. 1.0) agar kembang api tidak menutupi Pepe."""
        gc = int(px // CW)
        gr = int(py // CH)
        if 0 <= gr < GRID_ROWS and 0 <= gc < GRID_COLS:
            return self.pepe_shield[gr][gc]
        return 1.0

    def _tune_enhanced_pepe_color(
        self,
        c: int,
        r: int,
        col: Tuple[int, int, int],
        ch: str,
        is_edge: int,
        tag: int,
        is_mace_bulb: bool,
        is_baton_tip: bool,
        is_frogging_rib: bool,
    ) -> Tuple[int, int, int]:
        """Menyetel warna Pepe dengan detail tinggi, dual-rim lighting & ujung mayoret kuning."""
        red, grn, blu = col

        if is_mace_bulb:
            # Ujung bawah mayoret (Mace Bulb): Kuning keemasan bersinar terang!
            dist_center = math.hypot(c - 83.0, r - 64.0)
            core_k = clamp(1.0 - dist_center / 7.5, 0.0, 1.0)
            return (
                255,
                int(205 + 45 * core_k),
                int(55 + 95 * core_k),
            )

        if is_baton_tip:
            # Ujung atas tombak mayoret: Gradasi perak menuju kuning emas terang di pucuknya
            tip_k = clamp((27.0 - r) / 13.0, 0.0, 1.0)
            return (
                int(195 + 60 * tip_k),
                int(188 + 52 * tip_k),
                int(165 - 85 * tip_k),
            )

        if tag == 4:
            # Rongga mata & hidung tengkorak: hitam pekat dengan sedikit kilau merah-emas di pusat mata
            if r == 25 and c in (66, 67):
                return (220, 165, 65)  # Titik kilau hidup di dalam rongga mata tengkorak
            return (10, 8, 14)

        if tag == 3:
            # Tengkorak & tangan: kontras tulang gading tajam agar ekspresi tengkorak hidup
            return (
                int(clamp(red * 0.86 + 14, 110, 212)),
                int(clamp(grn * 0.84 + 10, 98, 194)),
                int(clamp(blu * 0.80 + 6, 82, 168)),
            )

        if tag == 8:
            # Batang tongkat mayoret tengah: perak-emas hangat
            return (205, 192, 152)

        if is_frogging_rib:
            # Kepang dada perak (frogging ribs) & garis celana: perak platinum tajam
            return (195, 208, 235)

        # Seragam hitam/charcoal The Black Parade dengan Dual-Rim Lighting:
        # Sisi kiri diterangi sinar bulan (perak-biru), sisi kanan diterangi cahaya emas mayoret
        if is_edge:
            if c < 64:
                return (108, 124, 158)  # Moonlit silver-blue rim
            else:
                return (132, 122, 98)   # Golden baton rim
        return (
            int(clamp(red * 0.74 + 14, 34, 72)),
            int(clamp(grn * 0.76 + 16, 38, 78)),
            int(clamp(blu * 0.80 + 20, 46, 94)),
        )

    # ==========================================================================
    # 1. LATAR BELAKANG LANGIT MALAM, KORONA BULAN & SILUET KOTA
    # ==========================================================================
    def _build_dark_cityscape(self) -> Tuple[pygame.Surface, List[Dict], List[Dict]]:
        surf = pygame.Surface((W, H))
        rng = random.Random(2026)

        base_r, base_g, base_b = 3, 4, 8
        surf.fill((base_r, base_g, base_b))

        sky_bottom = self.base_y
        for y in range(sky_bottom):
            t = y / float(sky_bottom)
            if t < 0.45:
                k = t / 0.45
                raw_r = 4 + 10 * k
                raw_g = 14 + 28 * k
                raw_b = 34 + 46 * k
            elif t < 0.75:
                k = (t - 0.45) / 0.30
                raw_r = 14 + 28 * k
                raw_g = 42 + 4 * k
                raw_b = 80 - 4 * k
            else:
                k = (t - 0.75) / 0.25
                raw_r = 42 + 32 * k
                raw_g = 46 + 6 * k
                raw_b = 76 + 10 * k

            r = int(base_r * (1.0 - BG_OPACITY) + raw_r * BG_OPACITY)
            g = int(base_g * (1.0 - BG_OPACITY) + raw_g * BG_OPACITY)
            b = int(base_b * (1.0 - BG_OPACITY) + raw_b * BG_OPACITY)
            pygame.draw.line(surf, (r, g, b), (0, y), (W, y))

        # Korona Cahaya Bulan Lembut (Radial Lunar Glow) di langit kiri atas
        moon_glow = pygame.Surface((W, H))
        moon_glow.fill((0, 0, 0))
        for rad in range(170, 10, -6):
            k = ((170 - rad) / 160.0) ** 2.1
            gr = int(38 * k)
            gg = int(42 * k)
            gb = int(54 * k)
            pygame.draw.circle(moon_glow, (gr, gg, gb), (self.moon_cx, self.moon_cy), rad)
        surf.blit(moon_glow, (0, 0), special_flags=pygame.BLEND_ADD)

        # Bintang-bintang malam
        sky_stars: List[Dict] = []
        for _ in range(380):
            sx = rng.randint(6, W - 6)
            band_y = 0.15 * H + 0.11 * H * math.sin(sx / float(W) * math.pi * 1.4 - 0.4)
            if rng.random() < 0.65:
                sy = int(clamp(rng.gauss(band_y, H * 0.11), 6, H * 0.58))
            else:
                sy = rng.randint(6, int(H * 0.60))

            dist_ratio = 1.0 - (sy / (H * 0.62))
            bright = rng.uniform(0.18, 0.52) * (0.4 + 0.6 * dist_ratio)
            sr = int(210 * bright)
            sg = int(225 * bright)
            sb = int(255 * bright)
            surf.set_at((sx, sy), (sr, sg, sb))

            if rng.random() < 0.25:
                sky_stars.append({
                    'px': (sx // CW) * CW,
                    'py': (sy // CH) * CH,
                    'ch': rng.choice(['.', '.', ':', '*', '+']),
                    'phase': rng.uniform(0.0, TAU),
                    'speed': rng.uniform(0.7, 2.0),
                    'base_lum': rng.uniform(0.25, 0.54),
                })

        # Siluet Gedung Kota
        silhouette_col = (2, 3, 6)
        edge_col = (14, 18, 28)

        city_specs = [
            (0.00, 0.025, 0.09, 'flat'),
            (0.02, 0.042, 0.20, 'pyramid'),
            (0.06, 0.018, 0.12, 'flat'),
            (0.075, 0.032, 0.19, 'stepped'),
            (0.105, 0.020, 0.08, 'flat'),
            (0.122, 0.022, 0.15, 'spire'),
            (0.142, 0.018, 0.07, 'flat'),
            (0.156, 0.028, 0.23, 'stepped'),
            (0.182, 0.016, 0.06, 'flat'),
            (0.195, 0.062, 0.14, 'dome'),
            (0.255, 0.028, 0.27, 'flat'),
            (0.285, 0.046, 0.36, 'pyramid'),
            (0.330, 0.016, 0.09, 'flat'),
            (0.344, 0.032, 0.24, 'pyramid'),
            (0.375, 0.048, 0.11, 'dome'),
            (0.420, 0.018, 0.10, 'flat'),
            (0.436, 0.036, 0.18, 'crenel'),
            (0.470, 0.018, 0.16, 'spire'),
            (0.486, 0.024, 0.20, 'flat'),
            (0.512, 0.022, 0.08, 'flat'),
            (0.532, 0.028, 0.11, 'flat'),
            (0.558, 0.026, 0.19, 'pyramid'),
            (0.584, 0.046, 0.20, 'twins'),
            (0.630, 0.032, 0.22, 'flat'),
            (0.662, 0.036, 0.21, 'flat'),
            (0.696, 0.018, 0.12, 'flat'),
            (0.712, 0.074, 0.35, 'empire'),
            (0.788, 0.040, 0.19, 'spires'),
            (0.828, 0.018, 0.09, 'flat'),
            (0.844, 0.042, 0.14, 'stepped'),
            (0.886, 0.034, 0.26, 'empire'),
            (0.922, 0.024, 0.09, 'flat'),
            (0.944, 0.036, 0.18, 'stepped'),
            (0.978, 0.025, 0.12, 'flat'),
        ]

        work_windows: List[Dict] = []

        for x_rat, w_rat, h_rat, style in city_specs:
            bx = int(x_rat * W)
            bw = max(14, int(w_rat * W))
            bh = int(h_rat * H)
            by = self.base_y - bh

            pygame.draw.rect(surf, silhouette_col, (bx, by, bw, bh))
            pygame.draw.rect(surf, edge_col, (bx, by, bw, bh), 1)

            if style == 'pyramid':
                peak_h = int(bw * 0.48)
                pts = [(bx - 2, by), (bx + bw + 2, by), (bx + bw // 2, by - peak_h)]
                pygame.draw.polygon(surf, silhouette_col, pts)
                pygame.draw.polygon(surf, edge_col, pts, 1)
            elif style == 'stepped':
                s1_w = int(bw * 0.65)
                s1_h = int(bh * 0.12)
                r1 = (bx + (bw - s1_w) // 2, by - s1_h, s1_w, s1_h)
                pygame.draw.rect(surf, silhouette_col, r1)
                pygame.draw.rect(surf, edge_col, r1, 1)
            elif style == 'spire':
                pygame.draw.line(surf, edge_col, (bx + bw // 2, by), (bx + bw // 2, by - 22), 2)
            elif style == 'dome':
                dome_r = int(bw * 0.28)
                pygame.draw.circle(surf, silhouette_col, (bx + bw // 2, by), dome_r)
                pygame.draw.circle(surf, edge_col, (bx + bw // 2, by), dome_r, 1)
            elif style == 'empire':
                t1_w = int(bw * 0.72)
                t2_w = int(bw * 0.44)
                pygame.draw.rect(surf, silhouette_col, (bx + (bw - t1_w) // 2, by - 16, t1_w, 16))
                pygame.draw.rect(surf, silhouette_col, (bx + (bw - t2_w) // 2, by - 30, t2_w, 14))
                pygame.draw.line(surf, edge_col, (bx + bw // 2, by - 30), (bx + bw // 2, by - 64), 2)
            elif style == 'twins':
                pygame.draw.rect(surf, silhouette_col, (bx + 3, by - 24, 6, 24))
                pygame.draw.rect(surf, silhouette_col, (bx + bw - 9, by - 24, 6, 24))
            elif style == 'spires':
                pygame.draw.line(surf, edge_col, (bx + 5, by), (bx + 5, by - 32), 2)
                pygame.draw.line(surf, edge_col, (bx + 13, by), (bx + 13, by - 26), 2)

            win_w, win_h = 4, 3
            pad_x, pad_y = 6, 9
            for wy in range(by + 12, self.base_y - 16, pad_y):
                for wx in range(bx + 6, bx + bw - 8, pad_x):
                    if rng.random() < 0.08:
                        warm_tone = rng.choice([
                            (138, 114, 44),
                            (124, 98, 36),
                            (152, 128, 56),
                        ])
                        work_windows.append({
                            'rect': pygame.Rect(wx, wy, win_w, win_h),
                            'color': warm_tone,
                            'phase': rng.uniform(0.0, TAU),
                            'speed': rng.uniform(0.15, 0.42),
                        })

        return surf, work_windows, sky_stars

    # ==========================================================================
    # 2. INISIALISASI ANIMASI ASCII AESTHETIC (BULAN BERSINAR, AURA & PARTIKEL)
    # ==========================================================================
    def _init_aesthetic_ascii_fx(self):
        rng = random.Random(777)

        # A. Bulan Sabit Bersinar Terang (Glowing Crescent Moon + 3 Halo Rings + Moonbeams)
        self.moon_core_cells = []
        self.moon_halo_cells = []
        mcx, mcy = self.moon_cx, self.moon_cy
        mr = 46.0

        for py in range(mcy - 115, mcy + 115, CH):
            for px in range(mcx - 115, mcx + 115, CW):
                dx = px - mcx
                dy = py - mcy
                d1 = math.hypot(dx, dy)
                d2 = math.hypot(dx - 17.0, dy + 7.0)
                ang = math.atan2(dy, dx)

                if d1 <= mr and d2 >= mr * 0.78:
                    # Tubuh utama Bulan Sabit (Sangat Terang & Bersinar)
                    is_rim = abs(d1 - mr) < 5.2 or abs(d2 - mr * 0.78) < 5.2
                    if is_rim:
                        ch = tangent_char(-math.sin(ang), math.cos(ang))
                        lum = 1.0
                    else:
                        ch = rng.choice(['@', '0', 'O', '*', '+'])
                        lum = rng.uniform(0.78, 0.96)
                    self.moon_core_cells.append((px, py, ch, lum, (px + py) % 9))
                elif mr < d1 <= 112.0:
                    # 3 Cincin Halo Konsentris & Sinar Bulan di sekeliling bulan
                    norm_d = (d1 - mr) / 66.0
                    if rng.random() < (0.48 * (1.0 - norm_d * 0.65)):
                        tch = tangent_char(-math.sin(ang), math.cos(ang))
                        self.moon_halo_cells.append((px, py, d1, ang, norm_d, tch))

        # B. Berkas Sinar Bulan (Diagonal ASCII Moonbeams menuju arah Pepe)
        self.moonbeams = []
        for i in range(28):
            dist_along = rng.uniform(55.0, 420.0)
            beam_ang = rng.uniform(0.18, 0.82)  # Menyorot serong kanan-bawah ke arah Pepe
            self.moonbeams.append({
                'dist': dist_along,
                'ang': beam_ang,
                'speed': rng.uniform(18.0, 34.0),
                'phase': rng.uniform(0.0, TAU),
                'ch': rng.choice(['.', ':', '+', '*', '~']),
            })

        # C. Pita Angin Malam (Night-Wind Nebula Ribbon)
        self.wind_ribbon_cells = []
        for gr in range(8, int(GRID_ROWS * 0.58), 2):
            for gc in range(4, GRID_COLS - 4, 3):
                px = gc * CW
                py = gr * CH
                nx = gc / float(GRID_COLS)
                ny = gr / float(GRID_ROWS)
                stream_y = 0.24 + 0.09 * math.sin(nx * TAU * 1.2 - 0.5)
                dist = abs(ny - stream_y)
                if dist < 0.088 and rng.random() < 0.38:
                    self.wind_ribbon_cells.append((px, py, nx, ny, dist))

        # D. Pusaran Aura Parade (Rising Spectral Wisps di sekeliling tubuh Pepe)
        self.spectral_aura = []
        for i in range(42):
            self.spectral_aura.append({
                'y_rel': rng.uniform(0.0, 1.0),
                'side': rng.choice([-1, 1]),
                'radius_x': rng.uniform(55.0, 155.0),
                'speed': rng.uniform(0.22, 0.48),
                'phase': rng.uniform(0.0, TAU),
                'ch': rng.choice(['*', '+', ':', '.', '~', 'o']),
                'is_gold': rng.random() < 0.45,
            })

        # E. Partikel Parade Malam (Abu Perak, Kelopak Mawar Merah Tua, Bara Emas)
        self.parade_particles = []
        for _ in range(72):
            kind = rng.choices(['ash', 'petal', 'ember'], weights=[0.42, 0.33, 0.25])[0]
            if kind == 'ash':
                col = (85, 96, 118)
                chars = ['.', ':', '~', '/', '\\']
            elif kind == 'petal':
                col = (178, 42, 58)
                chars = ['*', '%', '@', 'o', '+']
            else:
                col = (225, 178, 68)
                chars = ['+', '*', ':', '.']

            self.parade_particles.append({
                'x': rng.uniform(0, W),
                'y': rng.uniform(0, self.base_y),
                'vx': rng.uniform(-24.0, -9.0),
                'vy': rng.uniform(11.0, 28.0),
                'sway_amp': rng.uniform(9.0, 24.0),
                'sway_spd': rng.uniform(0.8, 2.2),
                'phase': rng.uniform(0.0, TAU),
                'chars': chars,
                'color': col,
            })

        # F. Bintang Jatuh (ASCII Shooting Stars)
        self.shooting_stars: List[Dict] = []
        self.next_meteor_time = 2.0

    def _draw_char(self, target: pygame.Surface, ch: str, px: int, py: int, color: Tuple[int, int, int]):
        if px < -CW or px >= W or py < -CH or py >= H:
            return
        r = max(0, min(255, int(color[0])))
        g = max(0, min(255, int(color[1])))
        b = max(0, min(255, int(color[2])))
        if r < 4 and g < 4 and b < 4:
            return
        key = (ch, (r, g, b))
        if key not in self.glyph_cache:
            self.glyph_cache[key] = self.font.render(ch, True, (r, g, b))
        target.blit(self.glyph_cache[key], (px, py))

    # ==========================================================================
    # 3. RENDERING LATAR, BULAN BERSINAR & ANIMASI ASCII AESTHETIC
    # ==========================================================================
    def _draw_background_and_aesthetic_fx(self, t: float, dt: float):
        # A. Salin latar kota malam ber-opacity rendah
        self.canvas_surf.blit(self.bg_static_surf, (0, 0))

        # Pantulan cahaya langit saat kembang api raksasa meledak (t >= 20s)
        total_fw_flash = sum(fw.flash_energy for fw in self.fireworks if fw.exploded)
        if total_fw_flash > 0.02:
            glow_val = int(min(28, total_fw_flash * 14))
            self.canvas_surf.fill((glow_val, int(glow_val * 0.85), int(glow_val * 1.15)), special_flags=pygame.BLEND_ADD)

        # B. Jendela kuning gedung
        for w in self.work_windows:
            wave = math.sin(t * w['speed'] + w['phase'])
            if wave > -0.65:
                flicker = 0.86 + 0.14 * math.sin(t * 2.0 + w['phase'])
                c = w['color']
                col = (int(c[0] * flicker), int(c[1] * flicker), int(c[2] * flicker))
                pygame.draw.rect(self.canvas_surf, col, w['rect'])

        # C. Bintang ASCII Berkedip di Langit Malam
        for st in self.sky_stars:
            twinkle = st['base_lum'] * (0.65 + 0.35 * math.sin(t * st['speed'] + st['phase']))
            col = (int(175 * twinkle), int(192 * twinkle), int(225 * twinkle))
            self._draw_char(self.canvas_surf, st['ch'], st['px'], st['py'], col)

        # D. BULAN SABIT BERSINAR TERANG (Dirender ke ascii_layer agar mendapat efek BLOOM penuh!)
        moon_pulse = 0.94 + 0.06 * math.sin(t * 2.1)
        for px, py, ch, lum, hsh in self.moon_core_cells:
            shimmer = lum * moon_pulse * (0.92 + 0.08 * math.sin(t * 3.0 + hsh))
            # Warna putih-emas hangat & perak bersinar terang
            col = (
                int(min(255, 255 * shimmer)),
                int(min(255, 246 * shimmer)),
                int(min(255, 208 * shimmer)),
            )
            self._draw_char(self.ascii_layer, ch, px, py, col)

        # 3 Cincin Halo Bulan yang berdenyut & berputar lembut
        for px, py, d1, ang, norm_d, tch in self.moon_halo_cells:
            wave = 0.5 + 0.5 * math.sin(d1 * 0.18 - t * 2.2 + 2.0 * ang)
            halo_lum = (1.0 - norm_d) * (0.35 + 0.65 * wave)
            if halo_lum > 0.22:
                ch = tch if wave > 0.72 else ('*' if halo_lum > 0.58 else (':' if halo_lum > 0.36 else '.'))
                col = (
                    int(min(255, 225 * halo_lum)),
                    int(min(255, 218 * halo_lum)),
                    int(min(255, 175 * halo_lum)),
                )
                self._draw_char(self.ascii_layer, ch, px, py, col)

        # Berkas Sinar Bulan (ASCII Moonbeams) yang mengalir turun ke arah Pepe
        for mb in self.moonbeams:
            cur_d = 52.0 + ((mb['dist'] + t * mb['speed']) % 380.0)
            fade_mb = math.sin(((cur_d - 52.0) / 380.0) * math.pi) * (0.55 + 0.45 * math.sin(t * 2.4 + mb['phase']))
            if fade_mb > 0.18:
                bx = int(self.moon_cx + math.cos(mb['ang']) * cur_d)
                by = int(self.moon_cy + math.sin(mb['ang']) * cur_d)
                self._draw_char(
                    self.ascii_layer,
                    mb['ch'],
                    bx,
                    by,
                    (int(165 * fade_mb), int(162 * fade_mb), int(135 * fade_mb))
                )

        # E. Pita Angin Malam (Night-Wind Nebula Ribbon)
        for px, py, nx, ny, dist in self.wind_ribbon_cells:
            w_val = ripple(nx * 6.0 - t * 0.45, ny * 8.0, t * 0.35)
            fade = (1.0 - dist / 0.088) * (0.5 + 0.5 * w_val)
            if fade > 0.24:
                ch = ':' if fade > 0.52 else ('.' if fade > 0.35 else ',')
                col = (int(48 * fade), int(62 * fade), int(88 * fade))
                self._draw_char(self.canvas_surf, ch, px, py, col)

        # F. Bintang Jatuh (ASCII Shooting Stars / Meteor)
        if not self.is_paused and t >= self.next_meteor_time:
            self.next_meteor_time = t + random.uniform(3.6, 6.5)
            self.shooting_stars.append({
                'x': random.uniform(W * 0.22, W * 0.88),
                'y': random.uniform(H * 0.04, H * 0.22),
                'vx': -random.uniform(280.0, 380.0),
                'vy': random.uniform(95.0, 150.0),
                'age': 0.0,
                'max_age': random.uniform(0.70, 1.15),
            })

        for mt in self.shooting_stars[:]:
            if not self.is_paused:
                mt['age'] += dt
                mt['x'] += mt['vx'] * dt
                mt['y'] += mt['vy'] * dt
            if mt['age'] >= mt['max_age']:
                self.shooting_stars.remove(mt)
                continue
            life = 1.0 - (mt['age'] / mt['max_age'])
            trail_chars = ['*', '+', '-', '~', ':', '.']
            for k_idx, tch in enumerate(trail_chars):
                tx = int(mt['x'] - mt['vx'] * k_idx * 0.018)
                ty = int(mt['y'] - mt['vy'] * k_idx * 0.018)
                b_k = life * (1.0 - k_idx / float(len(trail_chars))) * 0.85
                self._draw_char(
                    self.ascii_layer,
                    tch,
                    tx,
                    ty,
                    (int(210 * b_k), int(225 * b_k), int(255 * b_k))
                )

        # G. Lantai Parade Perspektif ASCII & Riak Pijakan Sepatu
        self._draw_ascii_parade_ground(t, dt)

        # H. Pusaran Aura Parade (Rising Spectral Wisps di sekitar Pepe agar tidak sepi)
        pepe_cx = W * 0.50
        for sa in self.spectral_aura:
            prog = (sa['y_rel'] + t * sa['speed']) % 1.0
            sy = self.base_y + 10.0 - prog * (H * 0.68)
            spiral = math.sin(prog * TAU * 1.6 + t * 1.8 + sa['phase'])
            sx = pepe_cx + sa['side'] * sa['radius_x'] + spiral * 28.0
            alpha = math.sin(prog * math.pi) * (0.55 + 0.45 * math.sin(t * 3.0 + sa['phase']))
            if alpha > 0.18:
                if sa['is_gold']:
                    scol = (int(225 * alpha), int(185 * alpha), int(75 * alpha))
                else:
                    scol = (int(135 * alpha), int(152 * alpha), int(195 * alpha))
                self._draw_char(self.ascii_layer, sa['ch'], int(sx), int(sy), scol)

        # I. Partikel Abu, Kelopak Mawar & Bara Malam
        for pt in self.parade_particles:
            if not self.is_paused:
                pt['x'] += (pt['vx'] + math.sin(t * pt['sway_spd'] + pt['phase']) * pt['sway_amp']) * dt
                pt['y'] += pt['vy'] * dt
                if pt['x'] < -10:
                    pt['x'] = W + 10
                if pt['y'] > self.base_y + 20:
                    pt['y'] = -10
                    pt['x'] = random.uniform(0, W)

            ch_idx = int(t * 3.2 + pt['phase']) % len(pt['chars'])
            ch = pt['chars'][ch_idx]
            tw = 0.68 + 0.32 * math.sin(t * 2.6 + pt['phase'])
            r, g, b = pt['color']
            self._draw_char(
                self.ascii_layer,
                ch,
                int(pt['x']),
                int(pt['y']),
                (int(r * tw), int(g * tw), int(b * tw))
            )

    def _draw_ascii_parade_ground(self, t: float, dt: float):
        """Menggambar lantai parade perspektif ASCII dengan riak pijakan sepatu Pepe."""
        scroll = (t * 24.0) if t >= MARCH_START else (t * 6.0)
        foot_cx = W // 2 - 12
        foot_cy = self.base_y + 26

        for rp in self.step_ripples[:]:
            if not self.is_paused:
                rp['r'] += dt * 125.0
                rp['alpha'] -= dt * 0.68
            if rp['alpha'] <= 0.02:
                self.step_ripples.remove(rp)

        for r_idx, py in enumerate(range(self.base_y, H, CH)):
            depth = (py - self.base_y) / float(max(1, H - self.base_y))
            row_step = max(2, int(4 - depth * 2))
            base_bright = 0.24 + 0.40 * depth

            for gc in range(0, GRID_COLS, row_step):
                px = gc * CW
                wx = (px + int(scroll * (0.4 + 0.8 * depth))) % 36
                is_grid_line = (r_idx % 2 == 0) or (wx < CW)
                if not is_grid_line:
                    continue

                ell_d = math.hypot((px - foot_cx) / 78.0, (py - foot_cy) / 18.0)
                shadow_factor = clamp(ell_d, 0.25, 1.0)

                ch = '-' if (r_idx % 3 == 0 and wx < CW * 2) else '.'
                lum = base_bright * shadow_factor

                ripple_boost = 0.0
                for rp in self.step_ripples:
                    d_rp = math.hypot((px - rp['x']) * 0.65, (py - rp['y']) * 2.2)
                    band = math.exp(-((d_rp - rp['r']) / 13.0) ** 2) * rp['alpha']
                    if band > ripple_boost:
                        ripple_boost = band

                if ripple_boost > 0.12:
                    ch = '~' if ripple_boost > 0.35 else ':'
                    lum = min(1.2, lum + ripple_boost * 0.85)
                    col = (int(75 * lum), int(85 * lum), int(115 * lum))
                    self._draw_char(self.ascii_layer, ch, px, py, col)
                else:
                    col = (int(40 * lum), int(48 * lum), int(68 * lum))
                    self._draw_char(self.canvas_surf, ch, px, py, col)

    # ==========================================================================
    # 4. RENDERING KEMBANG API BERVARIASI & PELINDUNG SILUET PEPE (t >= 20.0s)
    # ==========================================================================
    def _update_and_draw_fireworks(self, t: float, dt: float):
        if t < FIREWORKS_START:
            return

        # Luncurkan roket dengan variasi ketinggian (rendah, sedang, tinggi) &
        # variasi ukuran (kecil, sedang, besar) mulai t >= 20.0s
        if not self.is_paused and t >= self.next_fw_time:
            burst_count = self.fw_rng.choices([1, 2, 3], weights=[0.32, 0.48, 0.20])[0]
            zones = [
                ('left_flank', W * 0.06, W * 0.28),
                ('right_flank', W * 0.72, W * 0.94),
                ('inner_left', W * 0.28, W * 0.38),
                ('inner_right', W * 0.62, W * 0.72),
            ]
            self.fw_rng.shuffle(zones)
            for idx in range(burst_count):
                z_name, z_lo, z_hi = zones[idx % len(zones)]
                lx = self.fw_rng.uniform(z_lo, z_hi)

                # Variasi ketinggian: rendah (atas gedung), sedang (tengah), tinggi (atas)
                alt_tier = self.fw_rng.choices(
                    ['low', 'medium', 'high'],
                    weights=[0.33, 0.37, 0.30]
                )[0]

                # Variasi ukuran: jika dekat dengan siluet Pepe, batasi ukuran ke kecil/sedang
                # agar tidak mendominasi area tengah; di sisi luar bebas kecil/sedang/besar
                if z_name in ('inner_left', 'inner_right'):
                    size_tier = self.fw_rng.choices(['small', 'medium'], weights=[0.65, 0.35])[0]
                elif alt_tier == 'low':
                    size_tier = self.fw_rng.choices(['small', 'medium', 'large'], weights=[0.42, 0.43, 0.15])[0]
                else:
                    size_tier = self.fw_rng.choices(['small', 'medium', 'large'], weights=[0.30, 0.38, 0.32])[0]

                rocket = ASCIIFireworkRocket(
                    self.fw_rng,
                    lx,
                    float(self.base_y - 6),
                    altitude_tier=alt_tier,
                    size_tier=size_tier,
                )
                self.fireworks.append(rocket)

            self.next_fw_time = t + self.fw_rng.uniform(0.85, 1.55)

        for fw in self.fireworks[:]:
            if not self.is_paused:
                fw.update(dt, t)
            if fw.dead:
                self.fireworks.remove(fw)
                continue

            # Gambar percikan roket yang sedang meluncur naik (terlindung oleh pepe_shield)
            for asp in fw.AscendingSparks:
                sh = self._get_pepe_shield(asp['x'], asp['y'])
                if sh <= 0.05:
                    continue
                ak = (1.0 - (asp['age'] / asp['max_age'])) * sh
                self._draw_char(
                    self.ascii_layer,
                    '*' if ak > 0.5 else '.',
                    int(asp['x']),
                    int(asp['y']),
                    (int(255 * ak), int(215 * ak), int(110 * ak))
                )

            if not fw.exploded:
                # Kepala roket kuning-putih terang & ekor komet
                hx, hy = int(fw.x), int(fw.y)
                sh_head = self._get_pepe_shield(hx, hy)
                if sh_head > 0.05:
                    self._draw_char(
                        self.ascii_layer,
                        '^',
                        hx,
                        hy,
                        (int(255 * sh_head), int(250 * sh_head), int(210 * sh_head))
                    )
                    self._draw_char(
                        self.ascii_layer,
                        '*',
                        hx,
                        hy + CH,
                        (int(255 * sh_head), int(225 * sh_head), int(120 * sh_head))
                    )

                tail_len = len(fw.trail_history)
                for idx, (tx, ty) in enumerate(fw.trail_history):
                    sh_t = self._get_pepe_shield(tx, ty)
                    if sh_t <= 0.05:
                        continue
                    ratio = (idx + 1) / float(max(1, tail_len))
                    tch = '!' if ratio > 0.75 else ('|' if ratio > 0.45 else (':' if ratio > 0.2 else '.'))
                    c_val = ratio * 0.95 * sh_t
                    self._draw_char(
                        self.ascii_layer,
                        tch,
                        int(tx),
                        int(ty),
                        (int(255 * c_val), int(205 * c_val), int(95 * c_val))
                    )
            else:
                # 1. Cincin Gelombang Kejut (Shockwave Halo) sesuai skala ukuran ledakan
                if fw.shock_alpha > 0.05:
                    ring_pts = 20 if fw.size_tier == 'small' else (28 if fw.size_tier == 'medium' else 36)
                    pal_c = fw.palette[0]
                    for ri in range(ring_pts):
                        rang = (ri / float(ring_pts)) * TAU
                        rx = fw.burst_x + math.cos(rang) * fw.shock_radius
                        ry = fw.burst_y + math.sin(rang) * fw.shock_radius * 0.85
                        sh_r = self._get_pepe_shield(rx, ry)
                        if sh_r <= 0.05:
                            continue
                        rtch = tangent_char(-math.sin(rang), math.cos(rang))
                        sa = fw.shock_alpha * 0.75 * sh_r
                        self._draw_char(
                            self.ascii_layer,
                            rtch,
                            int(rx),
                            int(ry),
                            (int(pal_c[0] * sa), int(pal_c[1] * sa), int(pal_c[2] * sa))
                        )

                # 2. Bunga Api Radial (Terhalang otomatis oleh pepe_shield jika mendekati Pepe)
                for sp in fw.sparks:
                    if sp['age'] >= sp['max_age']:
                        continue
                    life = 1.0 - (sp['age'] / sp['max_age'])
                    fade = smooth(life)

                    if life < 0.26 and ((int(t * 28.0) + sp['seed']) % 3 == 0):
                        continue

                    r, g, b = sp['color']

                    # Ekor jejak setiap partikel kembang api
                    t_list = sp['tail']
                    t_total = len(t_list)
                    for t_idx, (tx, ty) in enumerate(t_list):
                        sh_tail = self._get_pepe_shield(tx, ty)
                        if sh_tail <= 0.05:
                            continue
                        t_k = ((t_idx + 1) / float(t_total + 1)) * fade * 0.68 * sh_tail
                        tch = '*' if t_k > 0.52 else (':' if t_k > 0.26 else '.')
                        self._draw_char(
                            self.ascii_layer,
                            tch,
                            int(tx),
                            int(ty),
                            (int(r * t_k), int(g * t_k), int(b * t_k))
                        )

                    sh_sp = self._get_pepe_shield(sp['x'], sp['y'])
                    if sh_sp <= 0.05:
                        continue

                    if life > 0.80:
                        ch = '@' if (sp['seed'] % 2 == 0) else '#'
                    elif life > 0.52:
                        ch = tangent_char(sp['vx'], sp['vy']) if (sp['seed'] % 2 == 0) else '*'
                    elif life > 0.28:
                        ch = '+' if (sp['seed'] % 2 == 0) else 'x'
                    else:
                        ch = '*' if (life < 0.18 and sp['seed'] % 4 == 0) else (':' if life > 0.14 else '.')

                    whiten = max(0.0, (life - 0.72) * 2.4)
                    cr = min(255, int((r * fade + 160 * whiten) * sh_sp))
                    cg = min(255, int((g * fade + 160 * whiten) * sh_sp))
                    cb = min(255, int((b * fade + 160 * whiten) * sh_sp))

                    self._draw_char(
                        self.ascii_layer,
                        ch,
                        int(sp['x']),
                        int(sp['y']),
                        (cr, cg, cb)
                    )

    # ==========================================================================
    # 5. TRANSISI MASUK MULUS, GERAKAN TENTARA HALUS & UJUNG MAYORET KUNING
    # ==========================================================================
    def _draw_pepe(self, t: float, dt: float):
        # Amplop transisi-ke-langkah (march_env): mulai naik secara mulus sejak t = 4.6s
        # sehingga tidak ada patahan/hentakan saat transisi masuk selesai!
        march_env = smoother((t - 4.6) / 2.2)

        # Fase langkah tentara yang halus dan berwibawa
        march_t = max(0.0, t - 4.6)
        phase = march_t * self.march_freq * TAU

        # Kurva langkah kaki C2-continuous (tanpa sudut patah)
        raw_swing = (1.0 - math.cos(phase)) * 0.5
        leg_swing = smoother(raw_swing) * march_env

        # Pantulan vertikal harmonik mulus (tanpa sudut lancip abs(cos))
        step_bounce_y = (math.cos(phase * 2.0) - 1.0) * 0.5 * 6.8 * march_env
        torso_sway_x = math.sin(phase) * 3.0 * march_env
        torso_tilt = math.sin(phase) * 0.028 * march_env

        ox = self.sprite_offset_c * CW
        oy = self.sprite_offset_r * CH

        waist_px, waist_py = ox + 63 * CW, oy + 60 * CH
        neck_px, neck_py = ox + 69 * CW, oy + 35 * CH
        l_shoulder_px, l_shoulder_py = ox + 51 * CW, oy + 39 * CH
        r_shoulder_px, r_shoulder_py = ox + 76 * CW, oy + 40 * CH
        f_hip_px, f_hip_py = ox + 56 * CW, oy + 61 * CH
        b_hip_px, b_hip_py = ox + 61 * CW, oy + 74 * CH

        baton_angle = math.sin(phase - 0.25) * 0.135 * march_env
        baton_pump_y = math.sin(phase) * 11.0 * march_env

        if t < MARCH_START:
            # ==================================================================
            # TRANSISI MASUK EKSTRA HALUS (QUINTIC SMOOTHER REVEAL & SHOCKWAVE)
            # ==================================================================
            flash = math.exp(-((t - FLASH_TIME) / 0.28) ** 2)
            ring_k = smoother((t - 0.15) / 2.3)
            aura_k = smoother((t - 1.5) / 2.3)
            fill_on = smoother((t - 3.1) / 2.3)

            if t > FLASH_TIME:
                front = (t - FLASH_TIME) * 0.72
                fade_shock = math.exp(-(t - FLASH_TIME) / 0.60)
                if fade_shock > 0.04:
                    for spx, spy, srad, stch in self.shock_cells:
                        band = math.exp(-((srad - front) / 0.026) ** 2) * fade_shock
                        if band > 0.16:
                            scol = (
                                int(min(255, 225 * band)),
                                int(min(255, 198 * band)),
                                int(min(255, 135 * band))
                            )
                            self._draw_char(self.ascii_layer, stch, spx, spy, scol)

        # Picu gelombang riak ASCII di lantai saat langkah kaki menginjak tanah
        if t >= MARCH_START:
            step_half = int((phase / math.pi))
            if step_half != self.last_step_half:
                self.last_step_half = step_half
                self.step_ripples.append({
                    'x': ox + 58 * CW + torso_sway_x,
                    'y': self.base_y + 24,
                    'r': 6.0,
                    'alpha': 0.90,
                })

        # ======================================================================
        # CAHAYA KUNING KEEMASAN DI KEDUA UJUNG TONGKAT MAYORET (TOP TIP & BULB)
        # ======================================================================
        # 1. Ujung Atas Tongkat Mayoret (c=136, r=15)
        top_tip_bx, top_tip_by = ox + 136 * CW, oy + 15 * CH
        top_rx, top_ry = rotate_point(top_tip_bx, top_tip_by, r_shoulder_px, r_shoulder_py, baton_angle)
        top_tip_x = top_rx + torso_sway_x
        top_tip_y = top_ry + step_bounce_y + baton_pump_y

        # 2. Ujung Bawah Tongkat Mayoret / Mace Bulb (c=83, r=64)
        bulb_bx, bulb_by = ox + 83 * CW, oy + 64 * CH
        bulb_rx, bulb_ry = rotate_point(bulb_bx, bulb_by, r_shoulder_px, r_shoulder_py, baton_angle)
        bulb_x = bulb_rx + torso_sway_x
        bulb_y = bulb_ry + step_bounce_y + baton_pump_y

        mayoret_glow_k = smoother((t - 2.2) / 2.0)
        if mayoret_glow_k > 0.05:
            # Gambar Halo Bintang Kuning Bersinar di Kedua Ujung Mayoret
            self._draw_golden_mayoret_halo(top_tip_x, top_tip_y, t, mayoret_glow_k, radius=18.0, is_top=True)
            self._draw_golden_mayoret_halo(bulb_x, bulb_y, t, mayoret_glow_k, radius=24.0, is_top=False)

            if not self.is_paused and random.random() < 0.72 * mayoret_glow_k:
                # Percikan emas dari ujung atas
                self.baton_sparks.append({
                    'x': top_tip_x + random.uniform(-4, 4),
                    'y': top_tip_y + random.uniform(-4, 4),
                    'vx': random.uniform(-18.0, 18.0),
                    'vy': -random.uniform(14.0, 34.0),
                    'age': 0.0,
                    'max_age': random.uniform(0.55, 1.05),
                    'ch': random.choice(['*', '+', 'o', ':', '.']),
                })
                # Percikan emas dari kepala gada bawah (Mace Bulb)
                if random.random() < 0.65:
                    ang_s = random.uniform(0.0, TAU)
                    self.baton_sparks.append({
                        'x': bulb_x + math.cos(ang_s) * 10.0,
                        'y': bulb_y + math.sin(ang_s) * 10.0,
                        'vx': math.cos(ang_s) * random.uniform(8.0, 22.0),
                        'vy': math.sin(ang_s) * random.uniform(8.0, 22.0) + 10.0,
                        'age': 0.0,
                        'max_age': random.uniform(0.50, 0.95),
                        'ch': random.choice(['*', '+', ':', '.']),
                    })

        for bsp in self.baton_sparks[:]:
            if not self.is_paused:
                bsp['age'] += dt
                bsp['x'] += bsp['vx'] * dt
                bsp['y'] += bsp['vy'] * dt
            if bsp['age'] >= bsp['max_age']:
                self.baton_sparks.remove(bsp)
                continue
            bk = smoother(1.0 - bsp['age'] / bsp['max_age'])
            self._draw_char(
                self.ascii_layer,
                bsp['ch'],
                int(round(bsp['x'])),
                int(round(bsp['y'])),
                (int(255 * bk), int(225 * bk), int(65 * bk))
            )

        # Animasi Helai Bulu Topi (Plume Feather Wisps) yang terlepas ditiup angin
        if t >= MARCH_START and not self.is_paused and random.random() < 0.28:
            plume_tip_x = ox + 108 * CW + torso_sway_x
            plume_tip_y = oy + 6 * CH + step_bounce_y
            self.plume_wisps.append({
                'x': plume_tip_x + random.uniform(-6, 6),
                'y': plume_tip_y + random.uniform(-4, 8),
                'vx': random.uniform(18.0, 42.0),
                'vy': random.uniform(6.0, 20.0),
                'age': 0.0,
                'max_age': random.uniform(1.1, 2.0),
                'ch': random.choice([')', '~', '\\', '/', ':', '.']),
            })

        for pw in self.plume_wisps[:]:
            if not self.is_paused:
                pw['age'] += dt
                pw['x'] += pw['vx'] * dt
                pw['y'] += (pw['vy'] + math.sin(t * 4.0 + pw['x'] * 0.05) * 12.0) * dt
            if pw['age'] >= pw['max_age']:
                self.plume_wisps.remove(pw)
                continue
            pk = smoother(1.0 - pw['age'] / pw['max_age']) * 0.85
            self._draw_char(
                self.ascii_layer,
                pw['ch'],
                int(round(pw['x'])),
                int(round(pw['y'])),
                (int(125 * pk), int(138 * pk), int(172 * pk))
            )

        # ======================================================================
        # RENDER SELURUH 4.007 TITIK KARAKTER PEPE
        # ======================================================================
        for node in self.pepe_nodes:
            c = node['c']
            r = node['r']
            ch = node['ch']
            col = node['color']
            tag = node['tag']
            is_edge = node['is_edge']
            is_mace_bulb = node['is_mace_bulb']
            is_baton_tip = node['is_baton_tip']
            is_rib = node['is_rib']

            bx = node['tx']
            by = node['ty']

            # Hitung posisi artikulasi sendi secara presisi sub-piksel
            if tag == 9:
                hip_angle = -0.36 * leg_swing
                rx, ry = rotate_point(bx, by, f_hip_px, f_hip_py, hip_angle)
                px = rx + torso_sway_x + 11.0 * leg_swing
                py = ry + step_bounce_y * 0.5 + 44.0 * leg_swing
            elif tag == 10:
                back_angle = 0.28 * leg_swing
                rx, ry = rotate_point(bx, by, b_hip_px, b_hip_py, back_angle)
                px = rx + torso_sway_x - 16.0 * leg_swing
                py = ry - 38.0 * leg_swing
            elif tag == 6:
                arm_angle = math.sin(phase) * 0.19 * march_env
                rx, ry = rotate_point(bx, by, l_shoulder_px, l_shoulder_py, arm_angle)
                px = rx + torso_sway_x
                py = ry + step_bounce_y
            elif tag in (7, 8):
                rx, ry = rotate_point(bx, by, r_shoulder_px, r_shoulder_py, baton_angle)
                px = rx + torso_sway_x
                py = ry + step_bounce_y + baton_pump_y
            elif tag in (2, 3, 4):
                head_angle = math.sin(phase - 0.15) * 0.045 * march_env
                rx, ry = rotate_point(bx, by, neck_px, neck_py, head_angle)
                px = rx + torso_sway_x
                py = ry + step_bounce_y
            elif tag == 1:
                lag = (16 - r) * 0.20
                whip_x = math.sin(phase - lag) * 8.5 * march_env
                whip_y = math.cos(phase - lag) * 3.2 * march_env
                px = bx + torso_sway_x + whip_x
                py = by + step_bounce_y + whip_y
            else:
                rx, ry = rotate_point(bx, by, waist_px, waist_py, torso_tilt)
                px = rx + torso_sway_x
                py = ry + step_bounce_y

            # Jika masih dalam fase transisi masuk (t < MARCH_START)
            if t < MARCH_START:
                rad = node['rad']
                ang = node['ang']
                around = node['around']

                edge_trace = 0.0
                if is_edge or tag in (5, 8) or is_mace_bulb:
                    edge_trace = smoother((ring_k * 1.08 - around) / 0.09) * (0.95 if is_edge else 0.60)

                puff = 0.5 + 0.5 * ripple(2.0 * ang, 5.0 * rad - 0.5 * t, 0.4 * t)
                reach = 0.55 * (0.65 + 0.55 * puff)
                core_wave = aura_k * math.exp(-max(0.0, rad - 0.08) / max(0.05, reach))
                if tag in (3, 7, 8) or is_rib or is_mace_bulb:
                    core_wave *= 1.38

                span = 1.25 * fill_on
                body_fill = fill_on * smoother((span - rad) / 0.20)

                heat = max(edge_trace * (1.0 - 0.5 * fill_on), core_wave * (1.0 - 0.6 * fill_on), body_fill)
                heat *= (1.0 + 0.72 * flash)

                if heat < 0.07:
                    continue

                if body_fill < 0.84:
                    if is_edge and edge_trace > core_wave:
                        ch_draw = node['t_ch']
                    else:
                        lvl = min(3, max(0, int(heat * 3.4)))
                        pool = POOLS[lvl]
                        ch_draw = pool[(node['hsh'] + int(t * 7.5 + rad * 12.0)) % len(pool)]
                else:
                    ch_draw = ch

                true_r, true_g, true_b = col
                blend_true = smoother((body_fill - 0.22) / 0.68)
                glow_r, glow_g, glow_b = 195, 162, 98

                vis = clamp(heat, 0.0, 1.25)
                r_out = (glow_r * (1.0 - blend_true) + true_r * blend_true) * vis + 42.0 * flash
                g_out = (glow_g * (1.0 - blend_true) + true_g * blend_true) * vis + 38.0 * flash
                b_out = (glow_b * (1.0 - blend_true) + true_b * blend_true) * vis + 28.0 * flash

                self._draw_char(self.ascii_layer, ch_draw, int(round(px)), int(round(py)), (int(r_out), int(g_out), int(b_out)))
                continue

            # ==================================================================
            # ANIMASI INTERNAL HIDUP PADA TUBUH PEPE SAAT MARCHING
            # ==================================================================
            cr, cg, cb = col
            ch_draw = ch

            if is_mace_bulb or is_baton_tip:
                # Ujung Mayoret Kuning Keemasan Berdenyut Terang
                gold_pulse = 0.90 + 0.18 * math.sin(t * 6.5 + node['hsh'])
                cr = min(255, int(cr * gold_pulse))
                cg = min(255, int(cg * gold_pulse))
                cb = min(255, int(cb * gold_pulse))
            elif is_rib:
                # Kilau cahaya perak berjalan di sepanjang tulang dada kepang (=)
                glint = max(0.0, math.sin(r * 0.35 - t * 4.2 + c * 0.08)) ** 4
                cr = min(255, int(cr + 55 * glint))
                cg = min(255, int(cg + 55 * glint))
                cb = min(255, int(cb + 45 * glint))
            elif is_edge:
                # Shimmer halus pada kontur tepi siluet
                pulse = 0.90 + 0.14 * math.sin(t * 3.4 + node['hsh'] * 0.7)
                cr, cg, cb = int(cr * pulse), int(cg * pulse), int(cb * pulse)
            elif tag in (1, 2, 5, 6, 7, 9, 10):
                # Gelombang kain seragam tertiup angin malam (living ASCII cloth ripple)
                cloth_wave = ripple(c * 0.14 - t * 2.2, r * 0.14, t * 0.7)
                if cloth_wave > 0.42:
                    pool = POOLS[1] if cloth_wave < 0.68 else POOLS[2]
                    ch_draw = pool[(node['hsh'] + int(t * 5.0)) % len(pool)]
                sheen = 1.0 + 0.18 * cloth_wave
                cr, cg, cb = int(cr * sheen), int(cg * sheen), int(cb * sheen)

            self._draw_char(self.ascii_layer, ch_draw, int(round(px)), int(round(py)), (cr, cg, cb))

    def _draw_golden_mayoret_halo(
        self,
        cx: float,
        cy: float,
        t: float,
        intensity: float,
        radius: float,
        is_top: bool,
    ):
        """Menggambar cincin cahaya kuning keemasan di ujung tongkat mayoret."""
        # Inti cahaya kuning terang
        core_col = (
            int(255 * intensity),
            int(242 * intensity),
            int(125 * intensity),
        )
        self._draw_char(self.ascii_layer, '@', int(round(cx)), int(round(cy)), core_col)

        # Sinar halo berputar di sekeliling ujung mayoret
        rays = 8 if is_top else 12
        for i in range(rays):
            ang = (i / float(rays)) * TAU + (t * 2.8 if is_top else -t * 2.2)
            pulse_r = radius * (0.72 + 0.28 * math.sin(t * 5.5 + i * 1.7))
            rx = cx + math.cos(ang) * pulse_r
            ry = cy + math.sin(ang) * pulse_r
            ch = '*' if i % 2 == 0 else '+'
            k = (0.65 + 0.35 * math.sin(t * 6.0 + i)) * intensity
            col = (
                int(255 * k),
                int(215 * k),
                int(55 * k),
            )
            self._draw_char(self.ascii_layer, ch, int(round(rx)), int(round(ry)), col)

    # ==========================================================================
    # KONTROL LAYAR & LOOP UTAMA
    # ==========================================================================
    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            self.window = pygame.display.set_mode(
                (self.screen_w, self.screen_h),
                pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE
            )
        else:
            self.window = pygame.display.set_mode((1200, 864), pygame.RESIZABLE)

    def restart(self):
        self.time_elapsed = 0.0
        self.fireworks.clear()
        self.baton_sparks.clear()
        self.plume_wisps.clear()
        self.step_ripples.clear()
        self.next_fw_time = FIREWORKS_START
        self.trail_surf.fill((0, 0, 0))

    def jump_to_fireworks(self):
        """Lompat langsung ke detik 20.0 untuk melihat kembang api raksasa."""
        self.time_elapsed = FIREWORKS_START
        self.next_fw_time = FIREWORKS_START

    def run(self):
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit()
                    return
                elif e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        pygame.quit()
                        return
                    elif e.key == pygame.K_F11:
                        self.toggle_fullscreen()
                    elif e.key == pygame.K_SPACE:
                        self.is_paused = not self.is_paused
                    elif e.key == pygame.K_r:
                        self.restart()
                    elif e.key == pygame.K_f:
                        self.jump_to_fireworks()
                    elif e.key == pygame.K_s:
                        pygame.image.save(self.window, f"mcr_pepe_{int(time.time())}.png")
                elif e.type == pygame.VIDEORESIZE and not self.is_fullscreen:
                    self.window = pygame.display.set_mode((e.w, e.h), pygame.RESIZABLE)

            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            if not self.is_paused:
                self.time_elapsed += dt

            # Bersihkan layer ASCII foreground untuk frame ini
            self.ascii_layer.fill((0, 0, 0))

            # 1. Gambar Latar Gelap, Bulan Bersinar Terang & Animasi ASCII Aesthetic
            self._draw_background_and_aesthetic_fx(self.time_elapsed, dt)

            # 2. Gambar Kembang Api Tinggi & Ledakan Besar (Mulai t >= 20.0s)
            self._update_and_draw_fireworks(self.time_elapsed, dt)

            # 3. Gambar Pepe (Ujung Mayoret Kuning, Animasi Kain & Gerakan Ekstra Halus)
            self._draw_pepe(self.time_elapsed, dt)

            # 4. Gabungkan Trail & Multi-Pass Additive Glow (Membuat Bulan, Mayoret & Kembang Api Bersinar)
            self.trail_surf.fill(self.trail_fade, special_flags=pygame.BLEND_MULT)
            self.trail_surf.blit(self.ascii_layer, (0, 0), special_flags=pygame.BLEND_MAX)

            self.canvas_surf.blit(self.trail_surf, (0, 0), special_flags=pygame.BLEND_MAX)
            self.canvas_surf.blit(
                glow_tint(blur_surface(self.trail_surf, 4, 5), 0.58),
                (0, 0),
                special_flags=pygame.BLEND_ADD
            )
            self.canvas_surf.blit(
                glow_tint(blur_surface(self.trail_surf, 8, 20), 0.34),
                (0, 0),
                special_flags=pygame.BLEND_ADD
            )

            # 5. Tampilkan ke Monitor
            win_w, win_h = self.window.get_size()
            if win_w == W and win_h == H:
                self.window.blit(self.canvas_surf, (0, 0))
            else:
                scale = min(win_w / W, win_h / H)
                sw, sh = int(W * scale), int(H * scale)
                scaled = pygame.transform.smoothscale(self.canvas_surf, (sw, sh))
                self.window.fill((3, 4, 8))
                self.window.blit(scaled, ((win_w - sw) // 2, (win_h - sh) // 2))

            pygame.display.flip()


if __name__ == "__main__":
    app = MCRBlackParadeApp()
    app.run()
